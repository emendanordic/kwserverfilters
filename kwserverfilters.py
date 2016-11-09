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

import argparse, ConfigParser, getpass, json, logging, os, re, sys
from collections import namedtuple

parser = argparse.ArgumentParser(description='Klocwork Module and View Updater')
parser.add_argument('--url', required=True,
    help='URL to the Klocwork server, e.g. "http://kw.server:8080"')
parser.add_argument('--user', required=False, default=getpass.getuser(),
    help='The username to use for connecting to the Klocwork server')
parser.add_argument('--re-project', required=False, default='',
    help='Regular expression for which matching projects will be processed')

parser.add_argument('--config-files', required=True,
    help='The configuration file(s) containing the modules and views to add\
    to the Klocwork server. See README for format information')
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
        # args.module_files, args.module_dir, args.view_files, args.view_dir,
        args.config_files,
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
        config_files,
        silent, logger):
        self.kwapicon = kwplib.KwApiCon(url=url, user=user, verbose=verbose)
        self.re_project = re_project
        # self.module_files = module_files
        # self.module_dir = module_dir
        # self.view_files = view_files
        # self.view_dir = view_dir
        self.config_files = config_files
        self.silent = silent
        self.logger = logger
        self.modules = dict()
        self.views = dict()

        self.projects = []

        self.config = ConfigParser.ConfigParser()
        self.parse_config_files()


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
                    'paths' : m_paths,
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
            for v_name, v_query in self.views.iteritems():
                action = 'create_view'
                if v_name in existing_views:
                    action = 'update_view'
                values = {
                    'project' : project,
                    'action' : action,
                    'name' : v_name,
                    'query' : v_query,
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

    def parse_config_files(self):
        for f in self.config_files.strip().split(','):
            self.parse_config_file(f)

    def parse_config_file(self, config_file):
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        for section in config.sections():
            items = dict(config.items(section))
            if not 'type' in items:
                sys.exit('Could not find type in section "{0}"'.format(section))
            item_type = items['type']
            if item_type == 'module':
                if section in self.modules:
                    sys.exit("Module '{0}' already defined".format(section))
                if not 'paths' in items:
                    sys.exit('Cannot find paths in module "{0}"'.format(section))
                self.logger.debug('Found module "{0}" with paths "{1}"'.format(
                    section, items['paths']
                ))
                self.modules[section] = items['paths']
            elif item_type == 'view':
                if section in self.views:
                    sys.exit("View '{0}' already defined".format(section))
                if not 'query' in items:
                    sys.exit('Cannot find paths in module "{0}"'.format(section))
                self.logger.debug('Found view "{0}" with query "{1}"'.format(
                    section, items['query']
                ))
                self.views[section] = items['query']
            else:
                sys.exit('Type is not module or view in section "{0}"'.format(section))





if __name__ == "__main__":
    main()
