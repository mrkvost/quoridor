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

def run():
    # INIT MLP WEIGHTS
    W_hid = tf.Variable(tf.truncated_normal([INPUT_LAYER_SIZE, HIDDEN_LAYER_SIZE], stddev=0.1))
    b_hid = tf.Variable(tf.constant(0.01, shape=[HIDDEN_LAYER_SIZE]))

    W_out = tf.Variable(tf.truncated_normal([HIDDEN_LAYER_SIZE, OUTPUT_LAYER_SIZE], stddev=0.1))
    b_out = tf.Variable(tf.constant(0.01, shape=[OUTPUT_LAYER_SIZE]))

    # INIT LAYERS
    input_layer = tf.placeholder(tf.float32, [None, INPUT_LAYER_SIZE])
    hidden_layer = tf.sigmoid(tf.matmul(input_layer, W_hid) + b_hid)
    output_layer = tf.matmul(hidden_layer, W_out) + b_out

    # PLACEHOLDER FOR DESIRED OUTPUT
    desired = tf.placeholder(tf.float32, [MINI_BATCH_SIZE, OUTPUT_LAYER_SIZE])

    # MEAN SQUARE ERROR
    mse = tf.reduce_mean(tf.square(desired - output_layer))

    # ONE TRAINING STEP
    train_step = tf.train.AdamOptimizer(LEARNING_RATE).minimize(mse)

    # INIT TENSORFLOW TRAINING
    session = tf.Session()
    init = tf.initialize_all_variables()
    session.run(init)
    saver = tf.train.Saver()

    # INIT GAME
    game = Quoridor2()
    context = QuoridorContext(game)
    heuristic = HeuristicPlayer(game)
    players = {
        YELLOW: {'name': 'heuristic', 'player': heuristic},
        GREEN: {'name': 'heuristic', 'player': heuristic},
    }
    game_count = 10000

    # Q-LEARNING
    state_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    next_state_vectors = np.zeros([MINI_BATCH_SIZE, INPUT_LAYER_SIZE])
    action_vectors = np.zeros([MINI_BATCH_SIZE])
    reward_vectors = np.zeros([MINI_BATCH_SIZE])
    desired_vectors = np.zeros([MINI_BATCH_SIZE, OUTPUT_LAYER_SIZE])

    context.reset(players=players)
    state = input_vector_from_game_state(context)
    state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])

    i = 0
    move = 0
    while i < game_count:
        heuristic.play(context)
        action = context.last_action
        next_state = input_vector_from_game_state(context)
        next_state = np.array(list(next_state)).reshape([1, INPUT_LAYER_SIZE])
        reward = context.is_terminal * (1 - context.state[0] * 2) * REWARD_FACTOR
        mq = 0
        # if not context.is_terminal:
            # if context.state[0] == GREEN:
                # mq = session.run(tf.reduce_min(output_layer), feed_dict={input_layer: next_state})
            # else:
                # mq = session.run(tf.reduce_max(output_layer), feed_dict={input_layer: next_state})

        new_q = reward + FUTURE_REWARD_DISCOUNT * mq


        desired_output_layer = session.run(output_layer, feed_dict={input_layer: state})
        desired_output_layer[0, action] = new_q

        input_vectors[move, :] = state
        desired_vectors[move, :] = desired_output_layer

        if context.is_terminal:
            i += 1
            print(i)
            context.reset(players=players)
            state = input_vector_from_game_state(context)
            state = np.array(list(state)).reshape([1, INPUT_LAYER_SIZE])
        else:
            state = next_state

        move += 1
        if move == MINI_BATCH_SIZE:
            # TRAINING
            session.run(train_step, feed_dict={input_layer: input_vectors,
                                               desired: desired_vectors})
            move = 0

    save_path = saver.save(session, "model.ckpt")
    print("Model saved in file: %s" % save_path)

    session.close()
