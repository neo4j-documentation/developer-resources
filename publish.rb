#!/usr/bin/env ruby
require 'rubygems'
require 'bundler/setup'

html_file=ARGV[0]
raise "Usage: feed me html files" unless html_file

def get_value(name, lines)
  (lines.find{ |l| l.match("^#{name}:.*") } || "").split(/:/).last.strip
end

lines = File.read(html_file).each_line.collect.to_a

post_name = html_file.gsub(/deploy\/(.+)\.html$/,"\\1")
title = get_value('title',lines)
level = get_value('level',lines)
author = get_value('author',lines)
email = get_value('email',lines)
developer_section_name = get_value('developer_section_name',lines)
developer_section_slug = get_value('developer_section_slug',lines)
optional_slug = get_value('slug',lines)

post_name = optional_slug unless optional_slug.empty?

html =  lines.join.gsub(/href="(?:\/developer\/)?(?:(?:\.\.|[a-zA-Z0-9_-]+)\/)*([^#:]+?)"/,'href="/developer/\1"')
                  .gsub(/\/developer\/+developer/,'/developer')
                  .gsub(/\/developer\/+docs/,'/docs')

#puts "header: #{title} / #{level} / #{author} / #{email} / #{developer_section_name} / #{developer_section_slug} / #{optional_slug}"

POST_TYPE='developer'
require 'rubypress'

blog_id  = ENV['BLOG_HOSTNAME']
username = ENV['BLOG_USERNAME']
password = ENV['BLOG_PASSWORD']


content =         { :post_type     => POST_TYPE,
                    :post_date     => Time.now-5*60,
                    :post_content  => html,
                    :post_title    => title,
                    :post_name     => post_name,
                    :post_status   => 'publish'
                    :custom_fields => [{ :key => "developer_section_name", :value => developer_section_name },
                                       { :key => "developer_section_slug", :value => "" }] # was developer_section_slug
                  }

puts "publishing: #{post_name}"

wp = Rubypress::Client.new(:host     => blog_id,
                           :username => username,
                           :password => password)

all_pages = wp.getPosts( :filter => {:post_type   => POST_TYPE,
                                     :number      => 1000})

puts "Got #{all_pages.length} pages from the database"
pages = all_pages.select { |page| page['post_name'] == post_name }
puts "Got #{pages.length} pages matching the post_name '#{post_name}'"

page = pages.sort_by {|hash| hash['post_id'] }.first

if page
  if page['custom_fields'] then
    content[:custom_fields].each{ |f|
       found = page['custom_fields'].find{ |field| field['key']==f[:key] }
       f['id']=found['id'] if found
    }
  end
  post_id = page['post_id'].to_i
  puts "Editing #{post_id} on _#{blog_id}_ custom-field #{content[:custom_fields].inspect}"

  raise "edit failed" unless wp.editPost(:blog_id => blog_id,
                                         :post_id => post_id,
                                         :content => content)
else
  puts "Making a new post for '#{title}' on _#{blog_id}_"
  raise "publish failed" unless wp.newPost(:blog_id => blog_id,
                                           :content => content)
end
