$(document).on('click','.slider_hidden',function(){
    //$('.slider').css('height',0)
    $('html,body').animate({scrollTop: window.innerHeight},500);
})
if(axios)axios.defaults.withCredentials=true;
//Vue.prototype.$axios = axios;
const jq=(datalist)=>{
        var temp=new URLSearchParams()
        for(key in datalist){
            temp.append(key,datalist[key])
        }
        return temp
    };
