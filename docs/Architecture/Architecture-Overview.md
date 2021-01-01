The Blue Alliance is a webapp that runs on [Google App Engine](https://cloud.google.com/appengine), a managed serverless platform running on Google's cloud.


### Why AppEngine?

There are a few reasons why Appengine is a good fit for TBA.
 - It is fully managed and serverless, so we don't have to worry about maintaining hardware. Instead, we can focus solely on writing our business logic
 - Eslastic capacity and supports autoscaling. This means we can seamlessly size our deployment based on instantaneous load. Since FRC traffic patterns are inherently spikey (on days teams register, many people refresh the site, for example), this lets us adjust to demand without needing a person to manually upscale the site
 - Generous free tier. This has gotten less true over time, but we used to be able to run the entire offseason within the free tier (there are too many offseason events these days, which is a good problem to have!). Since TBA is a community project, keeping costs down is an important consideration.

### The 10K Foot View

TBA is built on the following technologies:
 - [Google App Engine](https://cloud.google.com/appengine) to host the site. Take a look at the [overview page](https://cloud.google.com/appengine/docs/standard/python3/an-overview-of-app-engine) for more, especially the concept of "services"
 - [Flask](https://palletsprojects.com/p/flask/) for a webapp framework
 - [Jinja2](https://palletsprojects.com/p/jinja/) for HTML template rendering
 - [Google Cloud Datastore](https://cloud.google.com/datastore) as a persistent database
 - [Google Cloud Memorystore](https://cloud.google.com/memorystore) for a hosted, managed Redis cache
 - [Google Cloud Tasks](https://cloud.google.com/tasks) for asynchronous execution
 - [FRC Events API](https://frc-events.firstinspires.org/services/API/) as a source for official FRC data

The main webapp has two componenets: the "frontend" and the "backend", and they share the datastore between them. 

The frontend receives HTTP requests from users, reads data from the datastore, and renders a response. Responses can take the form of webpages that you load in your browser or API responses containing JSON representation of the underlying data.

The backend does not handle user-initiated requests. It instead servers requests triggered by App Engine's [cron service](https://cloud.google.com/appengine/docs/standard/python3/scheduling-jobs-with-cron-yaml). [Cron](https://en.wikipedia.org/wiki/Cron) is a means of schedulding tasks to run a predetermined time of day or a a preconfigured interval. We periodically run a job to fetch data from an upstream source (like FIRST's APIs), compute derived statistics based on data in the datastore, or do other noninteractive processing. In short, the backend will write data for the frontend to later read and display to users.

[[Architecture/tba-design-overview.png]]

### What Next

The best place to go next is to read about the [[data|Architecture-Data-Model]] to get a sense for how the pieces of the site fit together.
