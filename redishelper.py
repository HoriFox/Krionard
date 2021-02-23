import redis

#Байтовый конвентер
def convert(data):
	if isinstance(data, bytes):	return data.decode()
	if isinstance(data, (str, int)):return str(data)
	if isinstance(data, dict):	return dict(map(convert, data.items()))
	if isinstance(data, tuple):	return tuple(map(convert, data))
	if isinstance(data, list):	return list(map(convert, data))
	if isinstance(data, set):	return set(map(convert, data))

class RedisConnection:
	def __init__(self, **kwargs):
		self.connect = redis.Redis(**kwargs)

	def get_session(self, user_id, key=None):
		#try:
		value = convert(self.connect.hgetall(user_id))
		return value[key] if key else value
		#except self.connect.ConnectionError:
		#pass #TO DO

	def edit_session(self, id_user, key, value):
		session = self.get_session(id_user)
		session[key] = value
		return self.set_session(id_user, session)

	def set_session(self, user_id, value):
		#try:
		result = self.connect.hset(user_id, None, None, value)
		#if result:
		#    self.connect.expire(user_id, 360) <- ttl
		return result
		#except self.connect.ConnectionError:
		#    pass #TO DO

	def new_session(self, user_id):
		session = {"debug":"false", "history":"none", "context":"first"}
		return self.set_session(user_id, session)

	def get_connect(self):
		return self.connect

