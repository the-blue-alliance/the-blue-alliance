#!/usr/bin/ruby
require "youtube_it"
require "json"
require 'yaml'

cnf = YAML::load_file(File.join(File.dirname(File.expand_path(__FILE__)), 'config.yml'))
key = cnf["key"]
client = YouTubeIt::Client.new(:dev_key => key, :username => cnf["username"], :password => cnf["password"])

to_delete = ["2009GAL - QM63", "2011NEW"]
page = 1
loop do
	puts "querying videos on page #{page}..."
	videos = client.my_videos(:per_page => 50, :page => page)
	chopping_block = videos.videos.select{ |x| to_delete.include?(x.title.strip) || to_delete.include?(x.title.split("-").first.strip)}
	puts videos.videos.map(&:title).to_json
	puts "got #{chopping_block.length} to delete out of #{videos.videos.length}"
	break if  chopping_block.length == 0 && videos.videos.length < 50
	chopping_block.each {|v|
		id = v.video_id.split("video:").last
		begin
			puts "Deleting #{id} - #{v.title}"
			client.video_delete(id)
			sleep 5
		rescue => error
			puts "Couldnt delete #{id}"
			puts error
			sleep 5
		end
	}
	page += 1
end