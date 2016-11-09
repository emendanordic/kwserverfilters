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

Just create text config files with sections representing Modules or Views,
specifying a line for each module/view

E.g.

#### File: example_modules_views.txt
```
[Modules]
3rdparty = justatest,somethingelse
components = justatest,somethingelse

[Views]
*default* = -module:3rdparty
components = module:components
```

This defines two modules, "3rdparty" and "components", and two views,
"\*default\*" and "components"

python kwserverfilters.py --config-files example_modules_views.txt
-url http://myklocworkserver:8080

This will now create two modules called "components" and "3rdparty" and update
the default view (to exclude all code matching the regular expressions provided
in the 3rdparty module) and create the view "components" to include code only
matching the regular expressions given by the components module

To specify only certain projects for which to apply this change, use the
--re-project option to provide a regular expression for which matching projects
will be included

## Python version

Currently developed against python v2.7.x (same as comes packaged with klocwork - *kwpython*)
