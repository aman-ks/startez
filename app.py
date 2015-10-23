from flask import Flask, json, request, jsonify, abort, url_for, make_response
import redis, random, os
from flask.ext.httpauth import HTTPBasicAuth
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from time import time, ctime
from types import *
from rq import Queue
from search import keyword_search
from send_mail import t_email


auth = HTTPBasicAuth()
app = Flask(__name__)
app.config['SECRET_KEY']='startezifyoucan'
SENDGRID_API_KEY = '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'
app.redis = redis.StrictRedis(host='localhost', port= 6379, db=0)
q = Queue(connection = app.redis)



'''
Going to use these 2 methods directly:
pwd_context.verify : method takes a plain password and hash as argument and returns True if the password is correct or False if not.
pwd_context.encrypt : method takes a plain password as argument and returns a hash of it with the user.

'''





def generate_auth_token(investor_id, expiration=2592000):
	s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
	return s.dumps({ 'id': investor_id })

def verify_auth_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
        print data
    except SignatureExpired:
        return None # valid token, but expired
    except BadSignature:
        return None # invalid token
    user_data = app.redis.hgetall('investor'+':'+str(data['id']))
    print user_data
    return user_data


@auth.verify_password
def verify_password(email_or_token,plain_password):
	#first try to authenticate using token
	user_data = verify_auth_token(email_or_token)
	if not user_data:
		#try to authenticate with username password
	    bool = app.redis.hexists('allinvestors',email_or_token)
	    if bool:
	        investor_id = app.redis.hget('allinvestors',email_or_token)
	        password = app.redis.hget(investor_id,'password')
	        if not pwd_context.verify(plain_password, password):
	        	return False
	        elif pwd_context.verify(plain_password,password):
	        	return True
	    else:
	    	return False
	return True


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

@app.route('/api/token/<investor_id>')
@auth.login_required
def get_auth_token(investor_id):
    token = generate_auth_token(investor_id)
    return jsonify({ 'token': token.decode('ascii') })

@app.route("/user/<user_id>")
def get_users(user_id):
    query = 'user'+':'+user_id
    data = app.redis.hgetall(query)
    return jsonify(data)

@app.route("/user/<user_id>/pitch")
def get_pitches(user_id):
    only = request.args.get('only')
    if not only:
        query = 'user'+':'+user_id+':'+'pitch'
        data = app.redis.hgetall(query)
        return jsonify(data)

    elif only in ['product','traction','market','team','hcp']:
        query = 'user'+':'+user_id+':'+'pitch'
        data = app.redis.hgetall(query)
        
        data = data[only]
        return jsonify({'pitch':data})

    else:
        resp = only+' was not found!'
        return jsonify({'status':'not found','text':resp})

@app.route("/user/<user_id>/ratings")
def get_ratings(user_id):
    only = request.args.get('only')
    if element not in ['product','traction','market','team']:
        text = 'Sorry, given %s ratings are not available'%element
        return jsonify({'status':'not found','text':text})
    else:
        query = 'user'+':'+user_id+':'+element+':'+'rating'
        rating_list = app.redis.lrange(query,0,-1)
        if not rating_list:
            
            data = {'status':'unrated','all_rating':rating_list}
            return jsonify(data)
        else:
            data = {'status':'rated','all_rating':rating_list}
            return jsonify(data)        

@app.route("/feed")
def feed():
	q = request.args.getlist('q')
	if not q:	
	    last_id = app.redis.get('last_user')
	    last_id = int(last_id)
	    if last_id != 1000:
	    	pipe = app.redis.pipeline()
	        retrieve = ['user:'+str(x) for x in range(1000,last_id)]
	        retrieve = retrieve[::-1]
	        data = []

	        for user in retrieve:
	            pipe.hgetall(user)

	        data = pipe.execute()    
	        return jsonify({'data':data})
	else:
		last_id = app.redis.get('last_user')
		last_id = int(last_id)
		pipe = app.redis.pipeline()
		retrieve = ['user:'+str(x) for x in range(1000,last_id)]
		all_data = []

		for user in retrieve:
			pipe.hgetall(user)
		
		all_data = 	pipe.execute()
		'''
		Calling the keyword search function with data of all users and list of keywords : q
		'''
		print "q is : "+str(q)
		qu = q[0].split(' ')
		print qu
		result = keyword_search(qu, all_data)

		pipe1 = app.redis.pipeline()

		for user in result:
			pipe1.hgetall(user)

		search_result = pipe1.execute()	

		return jsonify({'data':search_result})        

@app.route("/pref-feed", methods=['POST'])
def nfeed():

    if request.json:

        sector = request.json.get('sector')
        location = request.json.get('location')
        stage = request.json.get('stage')
        last_id = app.redis.get('last_user')
        last_id = int(last_id)

        if sector and stage and location:
            retrieve = ['user:'+str(x) for x in range(1000,last_id)]
            data = {}

            for user in retrieve:
                s = app.redis.hget(user,'sector')
                l = app.redis.hget(user,'location')
                st = app.redis.hget(user,'stage')
                
                if s==sector and l==location and st==stage:
                    key_user_id = app.redis.hget(user,'id')
                    value_user_data = app.redis.hgetall(user)
                    data[key_user_id] = value_user_data 

            return jsonify({'data':data})

        else:
            return jsonify({'status':'not found','text':'Could not find data for the respective filters.'})
    

    elif not request.json:
        abort(404)

'''
REDIS DATA STRUCTURES
id                         - String
user:id                    - Hash - user_dict : product, team, market, traction, hcp, name, email, sector, stage, location, password, id, last_updated_time
user:id:pitch              - Hash - user_pitch_map
user:id:gotratedby         - List - user_got_rated_by : investor:id 

investor:id                - Hash - investor_dict : name, organisation, insti_email, source_referral_code, share_referral_code, id
investor:id:rated:user:id  - Hash - investor_rated_user_dict : product_rating, traction_rating, market_rating, team_rating, time
investor:id:rated          - Hash - investor_rated_map : user:id (average rating)

investors:signup:refcode   - List - signup_code_list
'''

@app.route("/", methods=['GET'])
def welcome_message():
	return "Welcome to StartEZ"

@app.route("/allinvestors", methods=['GET'])
#@auth.login_required
def get_investors():
    data = app.redis.hgetall('allinvestors')
    return jsonify(data)


@app.route("/investor/<investor_id>", methods=['GET'])
#@auth.login_required
def get_investor(investor_id):
    query = 'investor'+':'+investor_id
    data = app.redis.hgetall(query)
    return jsonify(data)



@app.route("/investors", methods=['POST'])
def create_investor():
    if request.json:

        last_inv_id = app.redis.get('last_investor')
        name = request.json.get('name')
        password = request.json.get('password')
        organisation = request.json.get('organisation')
        insti_email = request.json.get('insti_email')
        source_referral_code = request.json.get('source_referral_code')
         
        signup_code_list = app.redis.lrange('investors:signup:refcode',0,-1)

        if source_referral_code in signup_code_list:


            last_inv_id = int(last_inv_id) + 1
            new_inv_key = 'investor'+':'+str(last_inv_id)
            investor_dict = {'name':'','password':'','organisation':'','insti_email':'','source_referral_code':'','share_referral_code':'','credits':'100'}
            all_investors_key = 'allinvestors'
            if name and insti_email and password:
                investor_dict['id'] = last_inv_id
                investor_dict['name'] = name
                investor_dict['insti_email'] = insti_email
                #function has been used directly from passlib
                password_hash = pwd_context.encrypt(password)
                investor_dict['password'] = password_hash
                investor_dict['source_referral_code'] = source_referral_code
                
                referral_code = lambda name: name[0:3]+str(random.randint(100,999))
                
                investor_dict['share_referral_code'] = referral_code(name.upper())
                app.redis.lpush('investors:signup:refcode',investor_dict['share_referral_code'])
                app.redis.hmset(new_inv_key, investor_dict)
                app.redis.hset(all_investors_key, investor_dict['insti_email'], new_inv_key)
                app.redis.incr('last_investor')
                app.redis.save()


                subject = 'Thank you for signing up on StartEZ'
                text = 'Welcome to the StartEZ Platform'
                html = '<h2>Welcome to the StartEZ Platform</h2>'
                to = insti_email
                mail_result = q.enqueue(t_email, subject, to, text, html)
                print mail_result



                return jsonify({'data':investor_dict,'status':'done','text':'Investor with information has been initialised'})
        else:

            return jsonify({'status':'invalid code', 'text':'The Referral Code enterred by you is invalid'})       
    elif not request.json:
        abort(404)



@app.route("/investor/<investor_id>/photo", methods=['PUT'])
def update_investor_photo(investor_id):
    key = 'investor'+':'+investor_id
    data = app.redis.hgetall(key)

    if not data:
        return jsonify({'status':'not found','text':'Investor with id %s not found'%investor_id})
    elif 'name' in data.keys():
        photo_key = 'photo'
        value = request.files['photo']
        #remember to add a directory to save the images there, while on production.
        value.save(secure_filename(value.filename))
        app.redis.hset(key, photo_key, value.filename)
        return jsonify({'status':'done','text':'Investor photo has been set'})
    


    
@app.route("/investor/<investor_id>", methods=['DELETE'])
def delete_investor(investor_id):
    hash_name = 'investor'+':'+investor_id
    value = app.redis.hget(hash_name,'share_referral_code')
    app.redis.lrem('investors:signup:refcode', 1, value)
    app.redis.hdel(hash_name,'name','password','organisation','insti_email','source_referral_code','share_referral_code','id','credits','photo')

    return jsonify({'status':'done','text':'Deleted investor with id number %s'%investor_id})



@app.route("/investor/<investor_id>/rate/<user_id>", methods=['POST'])
def rate_user(investor_id, user_id):
    if request.json:
        investor_rated_user_dict = {}
        key = 'investor'+':'+investor_id+':'+'rated'+':'+'user'+':'+user_id
        user_key = 'user'+':'+user_id

        p_r = request.json.get('product_rating')
        m_r = request.json.get('market_rating')
        tr_r = request.json.get('traction_rating')
        t_r = request.json.get('team_rating')
        rating_time = ctime(time())
        print type(p_r), type(m_r), type(tr_r), type(t_r)

        if type(p_r) is FloatType and type(m_r) is FloatType and type(tr_r) is FloatType and type(t_r) is FloatType:
            investor_rated_user_dict['product_rating'] = p_r
            investor_rated_user_dict['traction_rating'] = tr_r
            investor_rated_user_dict['market_rating'] = m_r
            investor_rated_user_dict['team_rating'] = t_r
            investor_rated_user_dict['time'] = rating_time
            av_r = (p_r+t_r+m_r+tr_r)/4

            rv = app.redis.hset(user_key, 'product_rating', str(p_r))
            print "This is the return value for hset : "+str(rv)
            rv1 = app.redis.hset(user_key, 'traction_rating', str(tr_r))
            rv2 = app.redis.hset(user_key, 'market_rating', str(m_r))
            rv3 = app.redis.hset(user_key, 'team_rating', str(t_r))
            rv4 = app.redis.hset(user_key, 'average_rating', str(av_r))
            print "This is executing rv1 %d rv2 %d rv3 %d rv4 %d"%(rv1, rv2, rv3, rv4) 


            app.redis.hmset(key, investor_rated_user_dict)
            app.redis.save()
            return jsonify({'status':'done','text':'Investor with id '+investor_id+' has rated user with id '+user_id+' with ratings'+str(investor_rated_user_dict)+' .'})
        else:
            return jsonify({'status':'not rated','text':'Ratings are not of FloatType'})    


    elif not request.json:
        abort(404)    


@app.route("/investor/<investor_id>/favourite/<user_id>", methods=['GET'])
def favourite_user(investor_id, user_id):
    
    key = 'investor'+':'+investor_id+':'+'fav'
    user_key = 'user'+':'+user_id

    if app.redis.sismember(key, user_key):
        app.redis.srem(key,user_key)
        return jsonify({'status':'removed','text':'User was removed from favourites'})
    else:
        app.redis.sadd(key,user_key)
        return jsonify({'status':'added','text':'User was added to favourites'})    
    
'''
Endpoint below can be used when retrieving the contents of MyList/ Favourites.
Simple GET request from web/ mobile client will work.
'''

@app.route("/investor/<investor_id>/favourites", methods=['GET'])
def show_all_fav(investor_id):
    query = 'investor'+':'+investor_id+':'+'fav'
    members = app.redis.smembers(query)
    pipe = app.redis.pipeline()
    retrieve = list(members)
    
    data = []

    for user in retrieve:
        pipe.hgetall(user)

    data = pipe.execute()    
    return jsonify({'data':data})
    



@app.route("/investor/<investor_id>/getrating/<user_id>", methods=['GET'])
def get_rating_investor(investor_id, user_id):
	query = 'investor'+':'+investor_id+':'+'rated'+':'+'user'+':'+user_id
	data = app.redis.hgetall(query)
	return jsonify(data)
    
    
@app.route("/investor/refcode", methods=['GET'])
def get_all_refcodes():
    signup_code_list = app.redis.lrange('investors:signup:refcode',0,-1)
    return jsonify({'Working Referral Codes':signup_code_list})
    
if __name__ == "__main__":
    
    app.run(host='0.0.0.0', debug=True)