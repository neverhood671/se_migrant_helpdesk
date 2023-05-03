import chat_states as states

for k,v in states.ALL_STATES.items():
    if isinstance(v, states.MakeTopicPredictionNode):
        assert 'check_topic_prediction' in states.ALL_STATES.keys()
    elif isinstance(v, states.CheckTopicPredictionNode):
        assert 'head_topic_swedish' in states.ALL_STATES.keys()
        assert 'head_topic_bank' in states.ALL_STATES.keys()
        assert 'head_topic_pn' in states.ALL_STATES.keys()
        assert 'head_topic_apartment' in states.ALL_STATES.keys()
        assert 'head_topic_culture' in states.ALL_STATES.keys()
    elif isinstance(v, states.FeedbackNode):
        continue
    elif isinstance(v, states.SimpleOptionNode):
        if v.exit_node_id is not None:
            assert v.exit_node_id in states.ALL_STATES.keys()
        for o in v.options:
            assert o['next_node_id'] in states.ALL_STATES.keys()
    elif isinstance(v, states.PostnumberKomvuxSearcherNode):
        if v.exit_node_id is not None:
            assert v.exit_node_id in states.ALL_STATES.keys()
        assert v.unknown_postnumer_node_id in states.ALL_STATES.keys()
        assert v.komvux_exists_node_id in states.ALL_STATES.keys()
        assert v.komvux_doesnt_exists_node_id in states.ALL_STATES.keys()
    else:
        raise Exception(f'Unknown node type {k}: {v.__class__.__name__}')
