#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

html_file=ARGV[0]
raise "Usage: feed me html files" unless html_file

def get_value(lines)
  lines.shift.split(':').last.chomp[1..-1]
end

lines = File.read(html_file).each_line.collect.to_a

post_name = html_file.gsub(/deploy\/(.+)\.html$/,"\\1")
header = lines.shift
title = get_value(lines)
level = get_value(lines)
author = get_value(lines)
email = get_value(lines)
header = lines.shift

html =  lines.join
html = html.gsub(/href="(?:(?:\.\.|[a-zA-Z0-9_-]+)\/)*(.+?)"/,'href="/developer/\1"')
POST_TYPE='guide'
require 'rubypress'
blog_id  = ENV['BLOG_HOSTNAME']
username = ENV['BLOG_USERNAME']
password = ENV['BLOG_PASSWORD']


content =         { :post_type => "developer",
                    :post_date    => Time.now,
                    :post_content => html,
                    :post_title   => title,
                    :post_name => post_name
                  }

puts "publishing: #{post_name}"

wp = Rubypress::Client.new(:host     => blog_id,
                           :username => username,
                           :password => password)

all_pages = wp.getPosts( :filter => {:post_type   => "developer",
                                     :number      => 1000})
#

puts "Got #{all_pages.length} pages from the database"
pages = all_pages.select { |page| page['post_title'] == title }
puts "Got #{pages.length} pages matching the title"

page = pages.sort_by {|hash| hash['post_id'] }.first


if page
  post_id = page['post_id'].to_i
  puts "Editing #{post_id}"
  wp.editPost(:blog_id  => blog_id,
              :post_id => post_id,
              :content => content)
else
  puts "Making a new post for #{title}"
  puts wp.newPost(:blog_id => blog_id,
                  :content => content.merge({ :post_status  => "published"}))
end
