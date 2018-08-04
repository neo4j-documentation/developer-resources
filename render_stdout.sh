#!/bin/bash
cd "$(dirname "$0")"
export LANG=en_US.UTF-8
[[ -s "/Users/administrator/.rvm/scripts/rvm" ]] && source "/Users/administrator/.rvm/scripts/rvm" # Load RVM into a shell session *as a function*
rvm use 2.4.2 >/dev/null 2>&1
ruby /Users/administrator/repos/developer-resources/render_stdout.rb /dev/stdin
