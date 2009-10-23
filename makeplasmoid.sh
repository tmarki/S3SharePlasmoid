#!/bin/bash
zip -x ".git/*" -x ".project" -x ".settings/*" -x ".pydevproject" -x "*/*.pyc" -x ".gitignore" -x "makeplasmoid.sh" -r ../s3share_plasmoid.plasmoid .
