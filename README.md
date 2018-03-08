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
    **Content:** `{ people : [ Obama, Trump  ] }`

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
    **Content:** `[ actors.yml, students.yml  ]`

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

  `POS`

* **Data Params**

  {}

* **Success Response:**

  * **Code:** 200 <br />
    **Content:** `{}`

* **Error Response:**

  * **Code:** 404 NOT FOUND <br />
    **Content:** `{ error : "User doesn't exist" }`

  OR

  * **Code:** 401 UNAUTHORIZED <br />
    **Content:** `{ error : "You are unauthorized to make this request." }`

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
