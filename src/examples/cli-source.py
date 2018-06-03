import argparse
import sys

import configstacker as cs


class CliSource(cs.Source):
    def __init__(self, argv=None):
        self._parser = argparse.ArgumentParser()
        self._parser.add_argument('job_name')
        self._parser.add_argument('--job-cache', action='store_true')
        self._parser.add_argument('-r', '--job-retries', type=int, default=0)
        self._parser.add_argument('--host-url', default='localhost')
        self._parser.add_argument('--host-port', type=int, default=5050)
        self._parser.add_argument('-v', '--verbose', action='count', default=0)

        self._parsed_data = {}
        parsed = self._parser.parse_args(argv or sys.argv[1:])
        for (argument, value) in parsed._get_kwargs():
            tokens = argument.split('_')
            subsections, key_name = tokens[:-1], tokens[-1]
            last_subdict = cs.utils.make_subdicts(self._parsed_data, subsections)
            last_subdict[key_name] = value

        super(CliSource, self).__init__()

    def _read(self):
        return self._parsed_data


def main():
    cfg = CliSource()

    # just some demonstration code
    if cfg.verbose > 0:
        print('Job runner:\t{url}:{port}'.format(**cfg.host))
    if cfg.verbose > 1:
        cache_state = 'enabled' if cfg.job.cache else 'disabled'
        print('Job cache:\t%s' % cache_state)
        print('Max retries:\t%s' % cfg.job.retries)
    print('Start job %s' % cfg.job.name)


if __name__ == '__main__':
    main()
