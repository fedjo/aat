# Project Title

A web application to extract face and object annotations from videos using 
computer vision algorithms for face/object detection/recognition

### Prerequisites

On a GNU/Linux Debian Stretch machine install

* python 2.7
* docker
* docker-compose

### Installing

Clone git repository on your machine.
On a console run:

```
git clone https://github.com/fedjo/orca.git
```

Move into directory 'aat' and build
docker images

```
cd aat
./docker/build.sh dev
```
Then run containers using docker-compose

```
docker-compose up -d
```

## Running the tests


## Built With

* [Python 2.7](https://www.python.org/download/releases/2.7/) - The language used
* [Django 1.10](https://www.djangoproject.com/) - Python Web framework

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/fedjo/aat/tags).

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details


**Upload a face database**
----
  Upload a zip file containing the faces you want to find on videos.

* **URL**

  /model

* **Method:**

  `POST`

* **Data Params**

  model=[path of the zipfile]

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** `{ "people" : [ "Obama", "Trump"  ] }`

* **Sample Call:**

  ```javascript
    $.ajax({
      url: "/model",
      dataType: "json",
      type : "POST",
      data: new BinaryData('/path/to/file')
      success : function(r) {
        console.log(r);
      }
    });
  ```


**List all face databases**
----
  List all face databases that the recognizer has been trained with.

* **URL**

  /model

* **Method:**

  `GET`

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** `[ "actors.yml", "students.yml""  ]`

* **Sample Call:**

  ```javascript
    $.ajax({
      url: "/model",
      dataType: "json",
      type : "GET",
      success : function(r) {
        console.log(r);
      }
    });
  ```

**Annotation Process**
----
  Call the annotation process to generate automatic annotations.

* **URL**

  /annotate

* **Method:**

  `POST`

* **Data Params**

  `{
    "content": {"path": "/thesis_video/I148276[HD-VI].mp4"},
    "cascade": { "name": [1], "scale": "1.3", "neighbors": "5", "minx" : "25", "miny":"25", "framerate": 1  },
    "bounding_boxes": "True",
    "objdetector": {"framerate": 50},
    "transcription": {"input_language": "it", "output_language": "en"}
    }`

* **Success Response:**

  * **Code:** 200 <br />
  **Content:** `{
        "transcription": {
            "url: /static/I148276[HD-VI].srt"
        },
        "facedetection": {
                   "457.0": [
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                            "face": "Obama"
                            "probability": 0.56
                       },
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                            "face": "Obama"
                            "probability": 0.56
                       }
                   ],
                   "601.0": [
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                       },
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                       }
                   ],
               },
        "objectdetection": {
                   "457.0": [
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                            "class": "person"
                            "probability": 0.56
                       },
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                            "class": "dog"
                            "probability": 0.56
                       }
                   ],
                   ""601.0"": [
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                       },
                       {
                            "position": { "xaxis": 982, "yaxis": 181 },
                            "dimensions": { "width": 398, "height": 398 },
                       }
                   ],
                 }
  }`

* **Error Response:**

  * **Code:** 400 BAD REQUEST <br />
    **Content:** `{ error : "Bad JSON structure" }`

  OR

  * **Code:** 400 BAD REQUEST <br />
    **Content:** `{ error : "Input JSON is not appropriate" }`

* **Sample Call:**

  ```javascript
    $.ajax({
      url: "/annotate",
      dataType: "json",
      type : "POST",
      data: jsondata
      success : function(r) {
        console.log(r);
      }
    });
  ```
