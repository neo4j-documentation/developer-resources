#!/usr/bin/env ruby
#
html=ARGV[0]
raise "Usage: feed me html files" unless html

def get_value(lines)
  lines.shift.split(':').last.chomp[1..-1]
end

lines = File.read(html).each_line.collect.to_a

header = lines.shift
title = get_value(lines)
level = get_value(lines)
author = get_value(lines)
email = get_value(lines)
header = lines.shift

content=  lines.join

require 'rubypress'
blog_id  = ENV['BLOG_HOSTNAME']
username = ENV['BLOG_USERNAME']
password = ENV['BLOG_PASSWORD']

wp = Rubypress::Client.new(:host => blog_id,
                           :username => username,
                           :password => password)

post = wp.getPosts(:filter => {:post_type => 'page'}).select {|post| post['post_title'] == title}.first
content =         { :post_status  => "publish",
                    :post_date    => Time.now,
                    :post_content => content,
                    :post_title   => title }
if post
   wp.editPost(:blog_id => blog_id,
               :post_id => post['post_id'].to_i,
               :content => content)
else
  puts wp.newPost(:blog_id => blog_id,
                  :content => content.merge({ :post_type => 'page'}))
end
