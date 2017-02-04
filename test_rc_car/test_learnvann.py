from flat_game import test_carmunkv1
#from flat_game import test_carmunk
import numpy as np
import random
import csv
from nn import neural_net, LossHistory
import os.path
import timeit
import ann_class

import pymunk
from pymunk.vec2d import Vec2d
from pymunk.pygame_util import draw
import time

NUM_INPUT = 3
GAMMA = 0.9  # Forgetting.
TUNING = False  # If False, just use arbitrary, pre-selected params.


def train_net(params):

    filename = params_to_filename(params)

    observe = 50  # Number of frames to observe before training.
    epsilon = 1
    train_frames = 5000  # Number of frames to play.
    batchSize = params['batchSize']
    buffer = params['buffer']
    h=0
    # Just stuff used below.
    max_car_distance = 0
    car_distance = 0
    t = 0
    data_collect = []
    replay = []  # stores tuples of (S, A, R, S').

    loss_log = []
    history=[]
#    model=None

    # Create a new game instance.
    game_state = test_carmunkv1.GameState()

    # Get initial state by doing nothing and getting the state.
    _, state = game_state.frame_step((2))
#    print (observe)
    # Let's time it.
    start_time = timeit.default_timer()

    # Run the frames.
    trfn=True
    print(trfn)
    while t < train_frames:
#    while trfn==True:


        t += 1
        car_distance += 1
#        print(trfn)
##        trfn= t>observe and epsilon <0.1
#        print(t)
        trfn= t<observe and epsilon > 0.09
        if(trfn==False):
            print(trfn)

        # Choose an action.
        if random.random() < epsilon or t < observe:
            action = np.random.randint(0, 3)  # random
        else:
            # Get Q values for each action.
            [t1,qval] = ann_class.predict(state)
            action = (np.argmax(qval))  # best
            #print(action)

        # Take action, observe new state and get our treat.
        reward, new_state = game_state.frame_step(action)
	#print(np.matrix(state))
        # Experience replay storage.
        if(len(replay)<buffer):
           replay.append((state, action, reward, new_state))
        else:
             if(h < (buffer-1)):
                 h+=1
             else:
                 h=0
             replay[h]=(state, action, reward, new_state)
        start_time=time.time()
#        print(replay)
        # If we're done observing, start training.
        if t > observe:

            # If we've stored enough in our buffer, pop the oldest.
            if len(replay) > buffer:
                replay.pop(0)

            # Randomly sample our experience replay memory
            minibatch = random.sample(replay, batchSize)

            # Get training values.
            X_train, y_train = process_minibatch(minibatch)

            # Train the model on this batch.
#            history = LossHistory()
#            model.fit(
#                X_train, y_train, batch_size=batchSize,
#                nb_epoch=1, verbose=0, callbacks=[history]
#            )
#            loss_log.append(history.losses)
            model=ann_class.build_model(X_train, y_train, 100,1, print_loss=False)
            print("Frame value is {}" .format(t))
#            print("t by 10 value {}" .format(t%10))
            if t>observe:
#                print("frame value is {}".format(t))
               
                W1, b1, W2, b2 = model['W1'], model['b1'], model['W2'], model['b2']

                modelin=np.concatenate((W1,b1),axis=0)
                np.savetxt('modelin.txt',modelin)
                np.savetxt('W2.txt',W2)
                np.savetxt('b2.txt',b2)
            history=ann_class.calculate_loss(model, X_train, y_train)
            loss_log.append([history])

        # Update the starting state with S'.
#        b2 = model['b2']
        state = new_state
        #print("--% seconds" % (time.time()- start_time))
        # Decrement epsilon over time.
        
        
        if epsilon > 0.08 and t > observe:
            epsilon -= (1/train_frames)
        else:
            epsilon=epsilon
            
#        if epsilon < 0.1 and t>observe:
#            return
            
            
#        if(t==train_frames):
#            print("The final value is {}" .format(t))
        # We died, so update stuff.
#        if t==observe:
#            print("last frame value {}".format(t))
        if reward == -500:
            # Log the car's distance at this T.
            data_collect.append([t, car_distance])

            # Update max.
            if car_distance > max_car_distance:
                max_car_distance = car_distance

            # Time it.
            tot_time = timeit.default_timer() - start_time
            fps = car_distance / tot_time

            # Output some stuff so we can watch.
            print("Max: %d at %d\tepsilon %f\t(%d)\t%f fps" %
                  (max_car_distance, t, epsilon, car_distance, fps))

            # Reset.
            car_distance = 0
            start_time = timeit.default_timer()
#            b2 = model['b2']
#            print(b2)

        # Save the model every 25,000 frames.
        
#        if t % 4 == 0:
#            print("frame value is {}".format(t))
##            global model
#               
##            W1, b1, W2, b2 = model['W1'], model['b1'], model['W2'], model['b2']
#            W1=model['W1']
#            b1=model['b1']
#            W2=model['W2']
#            b2=model['b2']
#
#            modelin=np.concatenate((W1,b1),axis=0)
#            np.savetxt('modelin.txt',modelin)
#            np.savetxt('W2.txt',W2)
#            np.savetxt('b2.txt',b2)

    # Log results after we're done all frames.
    log_results(filename, data_collect, loss_log)
    return replay,loss_log

#def write_to_file(model,t):
#    if t % 4 == 0:
#        print("frame value is {}".format(t))
##        global model
#        W1, b1, W2, b2 = model['W1'], model['b1'], model['W2'], model['b2']
#        modelin=np.concatenate((W1,b1),axis=0)
#        np.savetxt('modelin.txt',modelin)
#        np.savetxt('W2.txt',W2)
#        np.savetxt('b2.txt',b2)
    
    
def log_results(filename, data_collect, loss_log):
    print(data_collect)
    print(loss_log)
    # Save the results to a file so we can graph it later.
    with open('results/sonar-frames/learn_data-' + filename + '.csv', 'w') as data_dump:
        wr = csv.writer(data_dump)
        wr.writerows(data_collect)

#    with open('results/sonar-frames/loss_data-' + filename + '.csv', 'w') as lf:
#        wr = csv.writer(lf)
#        for loss_item in loss_log:
#            wr.writerows(loss_item)


def process_minibatch(minibatch):
    """This does the heavy lifting, aka, the training. It's super jacked."""
    X_train = []
    y_train = []
    # Loop through our batch and create arrays for X and y
    # so that we can fit our model at every step.
    for memory in minibatch:
        # Get stored values.
        old_state_m, action_m, reward_m, new_state_m = memory
#        print("Old state is {}".format(old_state_m))
#        print("Memory value is {}".format(memory))
#        print("old state value is {}".format(old_state_m))
        # Get prediction on old state.
        [a,old_qval] = ann_class.predict(old_state_m)
#        print("Old q_val is {}".format(old_qval))
        # Get prediction on new state.
        [b,newQ] = ann_class.predict(new_state_m)
#        print("New q_val is {}".format(newQ))
        # Get our best move. I think?
        maxQ = np.max(newQ)
#        print("Max q_val is {}".format(maxQ))
        #print("old, new and max q are {} \n".format(old_qval))
        #print("new Q value: {} \n".format(newQ))
        
        #print("max Q value: {} \n".format(maxQ))
        y = np.zeros((1, 3))
        y[:] = old_qval[:]
        #print("Initial y value {} \n".format(y))
        # Check for terminal state.
        if reward_m != -500:  # non-terminal state
            update = (reward_m + (GAMMA * maxQ))
        else:  # terminal state
            update = reward_m
        # Update the value for the action we took.
        y[0][action_m] = update
        X_train.append(old_state_m.reshape(NUM_INPUT,))
        y_train.append(y.reshape(3,))
        #print("Final value of y{} \n".format(y))
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    y_train=np.argmax(y_train, axis=1)
#    print(y_train)

    return X_train, y_train


def params_to_filename(params):
    return str(params['nn'][0]) + '-' + str(params['nn'][1]) + '-' + \
            str(params['batchSize']) + '-' + str(params['buffer'])


def launch_learn(params):
    filename = params_to_filename(params)
    print("Trying %s" % filename)
    # Make sure we haven't run this one.
    if not os.path.isfile('results/sonar-frames/loss_data-' + filename + '.csv'):
        # Create file so we don't double test when we run multiple
        # instances of the script at the same time.
        open('results/sonar-frames/loss_data-' + filename + '.csv', 'a').close()
        print("Starting test.")
        # Train.
        model = neural_net(NUM_INPUT, params['nn'])
        train_net(model, params)
    else:
        print("Already tested.")


if __name__ == "__main__":
    if TUNING:
        param_list = []
        nn_params = [[164, 150], [256, 256],
                     [512, 512], [1000, 1000]]
        batchSizes = [40, 100, 400]
        buffers = [10000, 50000]

        for nn_param in nn_params:
            for batchSize in batchSizes:
                for buffer in buffers:
                    params = {
                        "batchSize": batchSize,
                        "buffer": buffer,
                        "nn": nn_param
                    }
                    param_list.append(params)

        for param_set in param_list:
            launch_learn(param_set)

    else:
        nn_param = [50, 50]
        print (nn_param)
        params = {
            "batchSize": 5,
            "buffer": 5000,
            "nn": nn_param
        }
#        model = neural_net(NUM_INPUT, nn_param)
        [replay,loss]=train_net(params)
        test=str(400)
        with open('results/sonar-frames/learn_data-' + test + '.csv', 'w') as data_dumpt:
            wr = csv.writer(data_dumpt)
            wr.writerows(loss)