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
function fetch_json(url,json){
    return fetch(url,{method:'POST',body:JSON.stringify(json)}).then(res=>res.json())
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
Promise.prototype.finally = function(callback) {
    var Promise = this.constructor;
    return this.then(function(value) {
        Promise.resolve(callback()).then(function() {
            return value;
        });
    },
    function(reason) {
        Promise.resolve(callback()).then(function() {
            throw reason;
        });
    });
}
function hasChanged(a,b){
    /**
     * 返回被修改参数集合
     * @method hasChanged
     * @param {dict} a 原始字典
     * @param {dict} b 修改后字典
     * @return {dict} 被修改过的参数字典
     */
    let change={}
    for(let i in a){
        if(b.hasOwnProperty(i) && a[i]!=b[i])change[i]=b[i]
    }
    for(let i in b){
        if(!a.hasOwnProperty(i) && b[i])change[i]=b[i]
    }
    return change
}
function deepCopy(obj) {
    let result = Array.isArray(obj) ? [] : {};
    for (let key in obj) {
        if (obj.hasOwnProperty(key)) {
            if (typeof obj[key] === 'object') {
                result[key] = deepCopy(obj[key]);   //递归复制
            } else {
                result[key] = obj[key];
            }
        }
    }
    return result;
}