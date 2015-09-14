
def keyword_search(query, data):
	'''
	Should return a list of users which have any of the keywords mentioned in the user object
	'''
	print query
	result_list = []
	for user_data in data:
		for keyword in query:
			if keyword in str(user_data):
				result_list.append('user:'+str(user_data['id']))
				break
			
	print "running fine"			
	return result_list