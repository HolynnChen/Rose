function toParams(param) {
    var result = ""
    for (let name in param) {
        if (typeof param[name] != 'function') {
            if(param[name])result += "&" + name + "=" + encodeURI(param[name]);
            else result+="&"+name+"="
        }
    }
    return result.substring(1)
}
function fetch_get(url){
    return fetch(url).then(response=>response.json())
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
function isListObjectValueEqual(a, b,within) {
    if(a.length!=b.length)return false
    for(let i of within){
        for(let j=0;j<a.length;j++){
            if(!a[j].hasOwnProperty(i)||!b[j].hasOwnProperty(i)||a[j][i]!=b[j][i])return false;
        }
    }
    return true
}
function checkObjectWithProp(a,name,value){
    if(a.hasOwnProperty(name) && a[name]==value)return true;
    return false
}
function findObjectInList(a,name,value){
    for(let i of a){
        if(checkObjectWithProp(i,name,value))return i
    }
    return null
}