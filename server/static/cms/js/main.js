$(document).on('click','.slider_hidden',function(){
    //$('.slider').css('height',0)
    $('html,body').animate({scrollTop: window.innerHeight},500);
})
$(document).on('click','.body_user_setting_block a',function(){
    url=$(this).pathname;
    
})
if(typeof axios!='undefined')axios.defaults.withCredentials=true;
//Vue.prototype.$axios = axios;
const jq=(datalist)=>{
        var temp=new URLSearchParams()
        for(key in datalist){
            temp.append(key,datalist[key])
        }
        return temp
    };
