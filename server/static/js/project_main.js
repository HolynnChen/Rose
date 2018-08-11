axios.defaults.withCredentials=true;
//Vue.prototype.$axios = axios;
const jq=(datalist)=>{
        var temp=new URLSearchParams()
        for(key in datalist){
            temp.append(key,datalist[key])
        }
        return temp
    };
