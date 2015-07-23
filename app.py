from flask import Flask, json, request, jsonify, abort, url_for, make_response
import redis, random
app = Flask(__name__)
app.redis = redis.StrictRedis(host='localhost', port= 6379, db=0)



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

    last_id = app.redis.get('last_user')
    last_id = int(last_id)
    if last_id != 1000:
        retrieve = ['user:'+str(x) for x in range(1000,last_id)]
        data = []

        for user in retrieve:
            f = app.redis.hgetall(user)
            data.append(f)
        return jsonify({'data':data})
    
    else:
        return 'Not found'        

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
investor:id:rated:user:id  - Hash - investor_rated_user_dict : product, traction, market, team (rating), time
investor:id:rated          - Hash - investor_rated_map : user:id (average rating)

investors:signup:refcode   - List - signup_code_list
'''

@app.route("/allinvestors", methods=['GET'])
def get_investors():
    data = app.redis.hgetall('allinvestors')
    return jsonify(data)

@app.route("/investor/<investor_id>", methods=['GET'])
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
            investor_dict = {'name':'','password':'','organisation':'','insti_email':'','source_referral_code':'','share_referral_code':'','id':'','credits':'100'}
            all_investors_key = 'allinvestors'
            if name and insti_email and password:
                investor_dict['id'] = last_inv_id
                investor_dict['name'] = name
                investor_dict['insti_email'] = insti_email
                investor_dict['password'] = password
                investor_dict['source_referral_code'] = source_referral_code
                
                referral_code = lambda name: name[0:3]+str(random.randint(100,999))
                
                investor_dict['share_referral_code'] = referral_code(name)
                app.redis.lpush('investors:signup:refcode',investor_dict['share_referral_code'])
                app.redis.hmset(new_inv_key, investor_dict)
                app.redis.hset(all_investors_key, new_inv_key, investor_dict['insti_email'])
                app.redis.incr('last_investor')
                app.redis.save()
                return jsonify({'status':'done','text':'Investor with information '+str(investor_dict)+'has been initialised'})
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
    
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port, debug=True)