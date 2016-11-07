# MIT License
#
# Copyright (c) 2016 Emenda Nordic
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from kwplib import kwplib

import argparse, getpass, json, logging, os, re, sys
from collections import namedtuple

parser = argparse.ArgumentParser(description='Klocwork Module and View Updater')
parser.add_argument('--url', required=True,
    help='URL to the Klocwork server, e.g. "http://kw.server:8080"')
parser.add_argument('--user', required=False, default=getpass.getuser(),
    help='The username to use for connecting to the Klocwork server')
parser.add_argument('--re-project', required=False, default='',
    help='Regular expression for which matching projects will be processed')

module_group = parser.add_mutually_exclusive_group(required=True)
view_group = parser.add_mutually_exclusive_group(required=True)
module_group.add_argument('--module-files',
    help='Location of the text files containing modules to add to the Klocwork\
    server.')
module_group.add_argument('--module-dir',
    help='Directory containing module text files to parse. Alternative to\
    --module-files.')
view_group.add_argument('--view-files',
    help='Location of the text files containing views to add to the Klocwork\
    server.')
view_group.add_argument('--view-dir',
    help='Directory containing view text files to parse. Alternative to\
    --view-files.')
parser.add_argument('--silent', required=False, dest='silent', action='store_true',
    help='Do not prompt user about performing updates')
parser.add_argument('--verbose', required=False, dest='verbose',
    action='store_true', help='Provide verbose output')

def main():
    args = parser.parse_args()
    logLevel = logging.INFO
    if args.verbose:
        logLevel = logging.DEBUG
    logging.basicConfig(level=logLevel,
        format='%(levelname)s:%(asctime)s %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')
    logger = logging.getLogger('kwserverfilters')

    kwserverfilters = KwServerFilters(args.url, args.user, args.re_project, args.verbose,
        args.module_files, args.module_dir, args.view_files, args.view_dir,
        args.silent, logger)
    try:
        kwserverfilters.get_project_list()
        kwserverfilters.add_modules()
        kwserverfilters.add_views()
    except SystemExit as e:
        logger.error(e)
        sys.exit(1)


class KwServerFilters:
    def __init__(self, url, user, re_project, verbose,
        module_files, module_dir, view_files, view_dir,
        silent, logger):
        self.kwapicon = kwplib.KwApiCon(url=url, user=user, verbose=verbose)
        self.re_project = re_project
        self.module_files = module_files
        self.module_dir = module_dir
        self.view_files = view_files
        self.view_dir = view_dir
        self.silent = silent
        self.logger = logger
        self.modules = dict()
        self.views = dict()

        self.projects = []

        self.modules = self.parse_files(self.module_files, self.module_dir)
        self.views = self.parse_files(self.view_files, self.view_dir)


    def get_project_list(self):
        self.logger.info('Getting list of projects...')
        values = {
            'action' : 'projects'
        }
        p_proj_match = re.compile(self.re_project)
        query_response = self.kwapicon.execute_query(values)
        if query_response.error_msg:
            sys.exit('Error with kwplib: "{0}"'.format(query_response.error_msg))
        for project in query_response.response:
            json_project = json.loads(project.strip())
            if 'name' in  json_project:
                p_name = json_project['name']
                if p_proj_match.match(p_name):
                    self.logger.debug(('Adding project "{0}" to list of'
                        ' projects to process'.format(json_project)))
                    self.projects.append(p_name)
                else:
                    self.logger.debug(('Skipping project "{0}" because it'
                        ' does not match regular expression'))
            else:
                sys.exit('Something wrong with json record "{0}"'.format(project))
        self.logger.debug('Projects that will be processed: "{0}"'.format(
            ', '.join(self.projects)
        ))

    def add_modules(self):
        self.logger.info('Creating/updating modules for projects...')
        if not self.silent:
            proceed = raw_input(('\nAre you sure you want to create/update'
                ' modules for projects {0}? [Y/N] '.format(', '.join(self.projects))))
            if not 'Y' == proceed.strip().upper():
                self.logger.info("Operation aborted")
                return
        for project in self.projects:
            self.logger.info('Updating project "{0}"'.format(project))
            existing_modules = self.get_items(project, 'modules')
            for m_name, m_paths in self.modules.iteritems():
                action = 'create_module'
                if m_name in existing_modules:
                    action = 'update_module'
                values = {
                    'project' : project,
                    'action' : action,
                    'name' : m_name,
                    'paths' : ','.join(m_paths),
                    'allow_all' : True
                }

                query_response = self.kwapicon.execute_query(values)
                if query_response.error_msg:
                    sys.exit('Error with kwplib "{0}"'.format(query_response.error_msg))
        self.logger.info('Modules created/updated successfully!')

    def add_views(self):
        self.logger.info('Creating/updating views for projects...')
        if not self.silent:
            proceed = raw_input(('\nAre you sure you want to create/update'
                ' views for projects {0}? [Y/N] '.format(', '.join(self.projects))))
            if not 'Y' == proceed.strip().upper():
                self.logger.info("Operation aborted")
                return
        for project in self.projects:
            self.logger.info('Updating project "{0}"'.format(project))
            existing_views = self.get_items(project, 'views')
            for v_name, v_query in self.modules.iteritems():
                action = 'create_view'
                if v_name in existing_views:
                    action = 'update_view'
                values = {
                    'project' : project,
                    'action' : action,
                    'name' : v_name,
                    'query' : ','.join(v_query),
                    'tags' : 'auto-created'
                }

                query_response = self.kwapicon.execute_query(values)
                if query_response.error_msg:
                    sys.exit('Error with kwplib "{0}"'.format(query_response.error_msg))
        self.logger.info('Views created/updated successfully!')

    def get_items(self, project, action):
        self.logger.debug('Retrieving existing {0} for project "{1}"'.format(action, project))
        items = []
        values = {
            'project' : project,
            'action' : action
        }
        for item in self.kwapicon.execute_query(values).response:
            items.append(json.loads(item)['name'])
        self.logger.debug('Retrieved {0} : {1}'.format(action, items))
        return items

    def parse_files(self, input_files, input_dir):
        files = []
        storage = {}
        if input_files:
            files = input_files.strip().split(',')
        elif input_dir:
            if not os.path.exists(input_dir) or not os.path.isdir(input_dir):
                sys.exit("Could not find directory '{0}'".format(input_dir))
            files = os.listdir(input_dir)
        self.logger.info('Retrieving modules/views from files {0}'.format(', '.join(files)))
        for i in files:
            if not os.path.exists(i):
                sys.exit("Could not find source file '{0}'".format(i))
            name = os.path.splitext(i)[0]
            values = []
            with open(i, 'r') as f:
                for line in f:
                    # ignore empty lines
                    if line.strip():
                        values.append(line.strip())
            if name in storage:
                sys.exit("Module/view '{0}' already defined".format(name))
            storage[name] = values
        return storage



if __name__ == "__main__":
    main()
