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

Just create text files with each line representing a path in a module or a search query in a view.
The name of the text file (without extension) will be used as the module/view name.

E.g.

#### File: 3rdparty.txt
```
**/boost/**
**/someotherlibrary/**
```

#### File: ProjectCode.txt
```
-module:3rdparty
```

python kwserverfilters.py --module-files 3rdparty.txt --view-files ProjectCode.txt -url http://myklocworkserver:8080

This will now create a module called 3rdparty and a view called ProjectCode that excludes all code matching the regular expressions provided in the 3rdparty.txt file for ALL projects

To specify only certain projects for which to apply this change, use the --re-project option to provide a regular expression for which matching projects will be included

## Python version

Currently developed against python v2.7.x (same as comes packaged with klocwork - *kwpython*)
