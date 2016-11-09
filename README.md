# kwserverfilters

## Introduction

This utility script allows you to easily maintain Klocwork modules and views
on your Klocwork server.

The whole purpose of this is to *enable simple yet powerful filtering of your
Klocwork issues*.

Modules - https://support.roguewave.com/documentation/klocwork/en/11-x/module/

Views - https://support.roguewave.com/documentation/klocwork/en/11-x/customizingyourviewoftheintegrationbuildanalysis/

## Usage

Simply run the script with --help to see the different options, e.g.

python kwserverfilters.py --help

## Module and View format

Just create text config files with each section representing a module or view
name, specifying a type (module/view) and then a list of paths for a module or a
query for a view (see below for more information)

E.g.

#### File: example_modules_views.txt
```
[components]
type = module
paths = justatest,somethingelse

[3rdparty]
type = module
paths = justatest,somethingelse

[*default*]
type = view
query = -module:3rdparty
```

This defines two modules, "components" and "3rdparty", and a view, "\*default\*"

python kwserverfilters.py --config-files example_modules_views.txt
-url http://myklocworkserver:8080

This will now create two modules called "components" and "3rdparty" and update
the default view to exclude all code matching the regular expressions provided
in the 3rdparty module file for ALL projects

To specify only certain projects for which to apply this change, use the
--re-project option to provide a regular expression for which matching projects
will be included

## Python version

Currently developed against python v2.7.x (same as comes packaged with klocwork - *kwpython*)
