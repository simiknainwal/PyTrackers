from flask import Flask,render_template,request

app=Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")
    # return 'Hello'


@app.route('/track')
def track():
    return render_template("track.html")
    # return 'Hello'



if __name__=="__main__":
    app.run(debug=True)