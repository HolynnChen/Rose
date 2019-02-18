function toParams(param) {
    var result = ""
    for (let name in param) {
        if (typeof param[name] != 'function') {
            result += "&" + name + "=" + encodeURI(param[name]);
        }
    }
    return result.substring(1)
}
function fetch_post(url,json){
    return fetch(url,{
        method:'post',
        headers:{
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        body:toParams(json)
    }).then(response=>response.json())
}