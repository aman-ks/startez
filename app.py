import redis
from flask import Flask, Response, json, request

app = Flask(__name__)
app.redis = redis.StrictRedis(host='localhost', port= 6379, db=0)

@app.route("/user/<user_id>")
def users(user_id):
    query = 'user'+':'+user_id
    data = app.redis.hgetall(query)
    resp = Response(json.dumps(data), status=200, mimetype='application/json')
    return resp

@app.route("/user/<user_id>/pitch")
def pitches(user_id):
    only = request.args.get('only')
    if only is None:
        query = 'user'+':'+user_id+':'+'pitch'
        data = app.redis.hgetall(query)
        resp = Response(json.dumps(data), status=200, mimetype='application/json')
        return resp

    else:
        query = 'user'+':'+user_id+':'+'pitch'
        data = app.redis.hgetall(query)
        
        if only=='product':
            
            data = data['product']
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp
        
        elif only=='traction':
    
            data = data['traction']
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp
        
        elif only=='market':
        
            data = data['market']
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp
        
        elif only=='team':
            
            data = data['team']
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp
        
        elif only=='hcp':
            
            data = data['hcp']
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp

        else:
            return only+' was not found!'    

@app.route("/user/<user_id>/ratings/<element>")
def ratings(user_id, element):
    if element not in ['product','traction','market','team']:
        return 'Sorry, given %s ratings are not available'%element
    else:
        query = 'user'+':'+user_id+':'+element+':'+'rating'
        rating_list = app.redis.lrange(query,0,-1)
        if not rating_list:
            #empty or unrated
            data = {'status':'unrated','all_rating':rating_list}
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp
        else:
            data = {'status':'rated','all_rating':rating_list}
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            return resp            

@app.route("/feed")
def feed():
    

    
if __name__ == "__main__":
    port = 5000
    app.run(host='0.0.0.0', port=port)