#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

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
POST_TYPE='guide'
require 'rubypress'
blog_id  = ENV['BLOG_HOSTNAME']
username = ENV['BLOG_USERNAME']
password = ENV['BLOG_PASSWORD']



wp = Rubypress::Client.new(:host     => blog_id,
                           :username => username,
                           :password => password)

all_pages = wp.getPosts( :filter => {:post_type   => POST_TYPE,
                                     :number      => 1000,
                                     :post_status => 'published'})

puts "Got #{all_pages.length} pages from the database"
pages = all_pages.select { |page| page['post_title'] == title }
puts "Got #{pages.length} pages matching the title"

page = pages.sort_by {|hash| hash['post_id'] }.first
content =         { :post_status  => "publish",
                    :post_date    => Time.now,
                    :post_content => content,
                    :post_title   => title }

if page
  post_id = page['post_id'].to_i
  puts "Editing #{post_id}"
  wp.editPost(:blog_id  => blog_id,
               :post_id => post_id,
               :content => content)
else
  puts "Making a new post for #{title}"
  puts wp.newPost(:blog_id => blog_id,
                  :content => content.merge({ :post_type => POST_TYPE}))
end
