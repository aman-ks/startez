from openpyxl import load_workbook
from app import app
import redis
import time

wb = load_workbook('data/data_new.xlsx')
s1 = wb['Sheet 1']
cell_range_product = s1['A2':'A132']
cell_range_traction = s1['B2':'B132']
cell_range_market = s1['C2':'C132']
cell_range_team = s1['E2':'E132']
cell_range_hcp = s1['F2':'F132']
cell_range_email = s1['G2':'G132']
cell_range_name = s1['H2':'H132']
cell_range_sector = s1['I2':'I132']
cell_range_stage = s1['J2':'J132']
cell_range_location = s1['K2':'K132']
# cell_range_time = s1['T2':'T33']

'''
REDIS DATA STRUCTURES
id 						   - String
user:id                    - Hash - user_dict
user:id:pitch              - Hash - user_pitch_map


'''

users_list = []
pitches_list = []
base_redis_key = 'user'
all_users_key = 'allusers'
first_user_id = 1000
first_investor_id = 1000
user_id = first_user_id

user_pitch_map = {'product':'','traction':'','market':'','team':'','hcp':'','time':''}
user_dict = {'product':'','traction':'','market':'','team':'','hcp':'','email':'','name':'','sector':'','stage':'','location':'','password':'startez123','id':'','last_updated_time':''}
ranges_list = [cell_range_product, cell_range_traction, cell_range_market, cell_range_team, cell_range_hcp, cell_range_email, cell_range_name, cell_range_sector, cell_range_stage, cell_range_location]

for p,t,m,te,h,e,n,s,st,l in zip(cell_range_product, cell_range_traction, cell_range_market, cell_range_team, cell_range_hcp, cell_range_email, cell_range_name, cell_range_sector, cell_range_stage, cell_range_location):
	user_dict['product']= p[0].value
	user_dict['traction']=t[0].value
	user_dict['market']=m[0].value
	user_dict['team']=te[0].value
	user_dict['hcp']=h[0].value
	user_dict['email']=e[0].value
	user_dict['name']=n[0].value
	user_dict['sector']=s[0].value
	user_dict['stage']=st[0].value
	user_dict['location']=l[0].value
	user_dict['id'] = user_id

	user_pitch_map['product'] = p[0].value
	user_pitch_map['traction'] = t[0].value
	user_pitch_map['market'] = m[0].value
	user_pitch_map['team'] = te[0].value
	user_pitch_map['hcp'] =  h[0].value
	user_pitch_map['time'] = float(time.time())
	user_pitch_map['human_readable_time'] = time.ctime(user_pitch_map['time'])
	user_dict['last_updated_time'] = user_pitch_map['human_readable_time']

	user = base_redis_key +":"+ str(user_id)                       #mapped to user_dict
	user_pitch = user +':'+'pitch'                                 #mapped to user_pitch_map
	user_product_rating = user +":"+"product"+":"+"rating"
	user_traction_rating = user +":"+"traction"+":"+"rating"
	user_market_rating = user +":"+"market"+":"+"rating"
	user_team_rating = user +":"+"team"+":"+"rating"

	pitches_list.append(user_pitch_map)
	users_list.append(user_dict)
	user_id = user_id+1                   #increment first_user_id everytime you make an entry in the database
    
    # '''Time to put all of this data into redis'''
    
	app.redis.hmset(user, user_dict)
	app.redis.hmset(user_pitch, user_pitch_map)
	app.redis.hset(all_users_key, user_dict['email'], user)
	app.redis.set('last_user',user_id)



		