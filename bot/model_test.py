# importing the module
import tracemalloc

tracemalloc.start()

import topics_modelling as model

topic = model.get_topic_for_message('I want to start SFI')
print(topic)
assert topic == 'swedish'

print(f'Spent memory: {tracemalloc.get_traced_memory()}')

tracemalloc.stop()
