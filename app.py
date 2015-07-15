from flask import Flask, json, request, jsonify, abort, url_for, make_response
import redis

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

@app.route("/user/<user_id>/ratings/<element>")
def get_ratings(user_id, element):
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
            return jsonify({'status':'not found','text':'Could not find the respective filters.'})
    

    elif not request.json:
        abort(404)

@app.route("/allinvestors", methods=['GET'])
def get_investors():
    pass
@app.route("/investor/<investor_id>", methods=['GET'])
def get_investor():
    pass


@app.route("/investors", methods=['POST'])
def create_investor():
    last_inv_id = app.redis.get('last_investor')
    new_inv_key = 'investor'+':'+last_inv_id
    pass

@app.route("/investor/<investor_id>", methods=['PUT'])
def update_investor_info():
    pass
@app.route("/investor/<investor_id>", methods=['DELETE'])
def delete_investor():
    pass
    
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port, debug=True)