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
