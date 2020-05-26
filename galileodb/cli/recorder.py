import argparse
import logging
import os
import signal
import time

import redis

from galileodb.factory import create_experiment_database_from_env
from galileodb.model import Experiment, generate_experiment_id
from galileodb.recorder import Recorder

logger = logging.getLogger(__name__)


def create_experiment(args):
    experiment_id = generate_experiment_id()
    if args.name:
        name = args.name
    else:
        name = experiment_id

    if args.creator:
        creator = args.creator
    else:
        creator = 'galileodb-recorder-' + str(os.getpid())

    now = time.time()

    return Experiment(experiment_id, name=name, creator=creator, start=now, created=now, status='RUNNING')


def main():
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGTERM, handle_sigterm)

    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=False, help='set name of experiment', default='')
    parser.add_argument('--creator', required=False, help='set name of creator', default='')
    args = parser.parse_args()

    # connect to redis eventbus
    rds = redis.Redis(
        host=os.getenv('galileo_redis_host', 'localhost'),
        port=int(os.getenv('galileo_redis_port', 6379)),
        decode_responses=True
    )

    # connect to experiment database
    exp_db = create_experiment_database_from_env()
    exp_db.open()

    # create and save the experiment
    exp = create_experiment(args)
    exp_db.save_experiment(exp)

    # main control loop
    recorder = Recorder(rds, exp_db, exp.id)
    try:
        logger.info('starting experiment recorder')
        recorder.start()
        logger.debug('storing node info keys')
        recorder.telemetry_recorder.save_nodeinfos()
        recorder.join()
    except KeyboardInterrupt:
        logger.debug('interrupt received')
        pass
    finally:
        exp_db.finalize_experiment(exp, 'FINISHED')
        logger.info('shutting down experiment recorder')
        if recorder:
            recorder.stop()
        exp_db.close()

    logger.info('recorder exiting')


def handle_sigterm(signal_number, _stack_frame):
    logger.debug('received signal %s', signal_number)
    raise KeyboardInterrupt


if __name__ == '__main__':
    main()