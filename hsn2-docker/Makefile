internal:
	docker build --force-rm -t ${IMGNAME} ${IMGSRC}

base:
	IMGNAME=hsn2/base IMGSRC=HSN2Base make internal

framework: base
	IMGNAME=hsn2/framework IMGSRC=Framework make internal

objectstore: base
	IMGNAME=hsn2/object-store IMGSRC=ObjectStore make internal

datastore: base
	IMGNAME=hsn2/data-store IMGSRC=DataStore make internal

feeders: base
	IMGNAME=hsn2/feeders IMGSRC=Feeders make internal

reporter: base
	IMGNAME=hsn2/reporter IMGSRC=Reporter make internal

webclient: base
	IMGNAME=hsn2/webclient IMGSRC=WebClient make internal

thug: 
	IMGNAME=hsn2/thug IMGSRC=HoneynetThug make internal

jssta: 
	IMGNAME=hsn2/jssta IMGSRC=JSSta make internal

console: base
	IMGNAME=hsn2/console IMGSRC=Console make internal

images: framework objectstore datastore feeders webclient reporter thug jssta console

startservices:
	docker run --name=framework -d -p 55672:55672 hsn2/framework
	echo "sleep to give framework a moment to start"; sleep 4
	docker run --name=datastore -d --link framework:framework hsn2/data-store
	echo "sleep to give datastore a moment to start"; sleep 4
	docker run --name=objectstore -d --link framework:framework --link datastore:datastore hsn2/object-store
	docker run --name=feeders -d --link framework:framework --link datastore:datastore hsn2/feeders
	docker run --name=webclient -d --link framework:framework --link datastore:datastore hsn2/webclient
	docker run --name=thug -d --link framework:framework --link datastore:datastore hsn2/thug
	docker run --name=reporter -d --link framework:framework --link datastore:datastore -p 5984:5984 hsn2/reporter
	docker run --name=jssta -d --link framework:framework --link datastore:datastore hsn2/jssta

startconsole:
	docker run -it --name=console --link framework:framework hsn2/console

start: startservices startconsole

stop:
	docker ps | grep hsn2  | cut -d" " -f 1 | xargs --no-run-if-empty docker stop --time=1
	docker ps -a | grep hsn2  | cut -d" " -f 1 | xargs --no-run-if-empty docker rm

clean: stop
	docker images | grep hsn2 | cut -d" " -f 1 | xargs --no-run-if-empty docker rmi
