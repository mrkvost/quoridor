import tensorflow as tf
import numpy as np
import time

from core.game import YELLOW, GREEN, Quoridor2
from core.context import QuoridorContext
from ai.players import HeuristicPlayer
from ai.utils import input_vector_from_game_state

# MLP parameters
INPUT_LAYER_SIZE = 151
HIDDEN_LAYER_SIZE = 100
OUTPUT_LAYER_SIZE = 140
LEARNING_RATE = 0.01
MINI_BATCH_SIZE = 100
REWARD_FACTOR = 100

# Q-learning parameters
FUTURE_REWARD_DISCOUNT = 0.99
GAME_COUNT = 10000

def run():
    # INIT MLP WEIGHTS
    W_hid = tf.Variable(tf.truncated_normal([INPUT_LAYER_SIZE, HIDDEN_LAYER_SIZE], stddev=0.01))
    b_hid = tf.Variable(tf.constant(0.01, shape=[HIDDEN_LAYER_SIZE]))

    W_out = tf.Variable(tf.truncated_normal([HIDDEN_LAYER_SIZE, OUTPUT_LAYER_SIZE], stddev=0.01))
    b_out = tf.Variable(tf.constant(0.01, shape=[OUTPUT_LAYER_SIZE]))

    # INIT LAYERS
    input_layer = tf.placeholder(tf.float32, [None, INPUT_LAYER_SIZE])
    hidden_layer = tf.sigmoid(tf.matmul(input_layer, W_hid) + b_hid)
    output_layer = tf.matmul(hidden_layer, W_out) + b_out

    # PLACEHOLDER FOR DESIRED OUTPUT
    desired = tf.placeholder(tf.float32, [None, OUTPUT_LAYER_SIZE])

    # COST FUNCTION - MEAN SQUARE ERROR
    mse = tf.reduce_mean(tf.square(desired - output_layer))

    # ONE TRAINING STEP
    train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(mse)


    # INIT GAME
    game = Quoridor2()
    context = QuoridorContext(game)
    heuristic = HeuristicPlayer(game)
    players = {
        YELLOW: {'name': 'heuristic', 'player': heuristic},
        GREEN: {'name': 'heuristic', 'player': heuristic},
    }

    # PLACEHOLDERS
    state_min_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    action_min_vector = np.zeros([MINI_BATCH_SIZE], dtype=np.int32)
    reward_min_vector = np.zeros([MINI_BATCH_SIZE])

    state_max_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    action_max_vector = np.zeros([MINI_BATCH_SIZE], dtype=np.int32)
    reward_max_vector = np.zeros([MINI_BATCH_SIZE])

    next_state_min_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    next_state_max_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])

    desired_vectors = tf.Variable(tf.zeros([MINI_BATCH_SIZE, OUTPUT_LAYER_SIZE]))
    des = tf.Variable(tf.zeros([MINI_BATCH_SIZE * OUTPUT_LAYER_SIZE]))

    # INIT TENSORFLOW
    session = tf.Session()
    init = tf.initialize_all_variables()
    session.run(init)
    saver = tf.train.Saver()

    context.reset(players=players)
    state = input_vector_from_game_state(context)
    state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])

    i = 0
    move_min = 0
    move_max = 0
    while i < GAME_COUNT:
        if context.state[0] == GREEN: # min turn
            # store current state
            state_min_vectors[move_min, :] = state

            # proceed to next state
            heuristic.play(context)
            next_state = input_vector_from_game_state(context)
            next_state = np.array(list(next_state)).reshape([1, INPUT_LAYER_SIZE])

            # store action
            action_min_vector[move_min] = (140 * move_min) + context.last_action

            # store reward
            reward_min_vector[move_min] = context.is_terminal * (1 - context.state[0] * 2) * REWARD_FACTOR

            # store next state
            next_state_min_vectors[move_min, :] = next_state

            move_min += 1
        else: # max turn
            # store current state
            state_max_vectors[move_max, :] = state

            # proceed to next state
            heuristic.play(context)
            next_state = input_vector_from_game_state(context)
            next_state = np.array(list(next_state)).reshape([1, INPUT_LAYER_SIZE])

            # store action
            action_max_vector[move_max] = (140 * move_max) + context.last_action

            # store reward
            reward_max_vector[move_max] = context.is_terminal * (1 - context.state[0] * 2) * REWARD_FACTOR

            # store next state
            next_state_max_vectors[move_max, :] = next_state

            move_max += 1


        if context.is_terminal:
            i += 1
            print('GAME ', i)
            context.reset(players=players)
            state = input_vector_from_game_state(context)
            state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])
        else:
            state = next_state

        if move_min == MINI_BATCH_SIZE:
            mq = session.run(tf.reduce_min(output_layer, reduction_indices=1), feed_dict={input_layer: next_state_min_vectors})
            new_q = tf.add(FUTURE_REWARD_DISCOUNT * mq, reward_min_vector)
            desired_vectors.assign(session.run(output_layer, feed_dict={input_layer: state_min_vectors}))
            des.assign(tf.reshape(desired_vectors, [140 * 100]))
            des.assign(tf.scatter_update(des, action_min_vector, new_q))
            desired_vectors.assign(tf.reshape(des, [100, 140]))

            session.run(train_step, feed_dict={input_layer: state_min_vectors, desired: desired_vectors.eval(session=session)})

            move_min = 0

        if move_max == MINI_BATCH_SIZE:
            mq = session.run(tf.reduce_max(output_layer, reduction_indices=1), feed_dict={input_layer: next_state_max_vectors})
            new_q = tf.add(FUTURE_REWARD_DISCOUNT * mq, reward_max_vector)
            desired_vectors.assign(session.run(output_layer, feed_dict={input_layer: state_max_vectors}))
            des.assign(tf.reshape(desired_vectors, [140 * 100]))
            des.assign(tf.scatter_update(des, action_max_vector, new_q))
            desired_vectors.assign(tf.reshape(des, [100, 140]))

            session.run(train_step, feed_dict={input_layer: state_max_vectors, desired: desired_vectors.eval(session=session)})

            move_max = 0

    save_path = saver.save(session, "model.ckpt")
    print("Model saved in file: %s" % save_path)

    session.close()
