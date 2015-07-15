from flask import Flask, json, request, jsonify, abort, url_for, make_response
import redis

app = Flask(__name__)
app.redis = redis.StrictRedis(host='localhost', port= 6379, db=0)



@app.route("/user/<user_id>")
def users(user_id):
    query = 'user'+':'+user_id
    data = app.redis.hgetall(query)
    return jsonify(data)

@app.route("/user/<user_id>/pitch")
def pitches(user_id):
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
def ratings(user_id, element):
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

@app.route("/feed", methods= ['POST','GET'])
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

    
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port, debug=True)