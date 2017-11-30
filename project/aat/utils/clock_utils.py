from django.conf import settings
import time
import timeit
import os

class Clock:

    @classmethod
    def time(self, func):
	def timed(*args, **kwargs):
	    t_start = time.time()
	    result = func(*args, **kwargs)
	    t_end = time.time()

	    f = open(os.path.join(settings.MEDIA_ROOT, 'timelapse.log'), 'a')
	    f.write('---Decorator time---\n')
	    f.write('%r() %2.2f sec\n' % (func.__name__,  t_end-t_start))
	    f.close()
	    return result

	return timed


    @classmethod
    def timeit(self, func):
	def timed(*args, **kwargs):

	    def wrapper(f, *arg, **kw):
		def wrapped():
		    return f(*args, **kwargs)
		return wrapped

	    wrapped = wrapper(func)
	    f = open(os.path.join(settings.MEDIA_ROOT, 'timelapse.log'), 'a')
	    f.write('---Decorator time-IT---\n')
	    f.write('%r() %2.2f sec\n' % (func.__name__, timeit.timeit(wrapped)))
	    f.close()
	    return

	return timed

