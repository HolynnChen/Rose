/*
creator: HolynnChen
update:  2018.12.13 19:30
version: 0.46
reason:  fix some bug
*/
function copy(text)
    {
        var oInput = document.createElement('textarea');
        oInput.value = text;
        document.body.appendChild(oInput);
        oInput.select(); // 选择对象
        document.execCommand("Copy"); // 执行浏览器复制命令
        document.body.removeChild(oInput)
        alert('已复制到剪辑版');
    }

new Vue({
    el:'#app',
    data(){
      return {text:[],input:true,origin:localStorage.getItem('origin')}
    },
    methods:{
        submit(event){
            event.preventDefault();
            console.log('start')
            let temp=$('#translate_input').val()
            while(temp.indexOf('\n\n\n')>-1)temp=temp.replace('\n\n\n','\n\n')
            for(let i of temp.split('\n\n')){
              if(i.length>5000){
                alert('第'+i.toString()+'段过长')
                return
              }else if (i.replace(' ','').length==0){
                alert('第'+i.toString()+'段不能为空段')
                return
              }
            }
            $('.mask').toggleClass('mask_hidden')
            let time=setTimeout(function(){
                console.log('in')
                $('.mask').stop().animate({ opacity: 1 }, 400)
            },500)
            $.post('/translate',{data:temp},(resp)=>{
                console.log(resp)
                clearTimeout(time)
                temp=temp.split('\n\n')
                let fool=[]
                for(let i=0;i<temp.length;i++){
                  fool.push([i,temp[i],resp['youdao']?resp['youdao'][i]:'',resp['google']?resp['google'][i]:''])
                }
                localStorage.setItem('origin',JSON.stringify(fool));
                localStorage.setItem('save',JSON.stringify([]));
                this.text=fool
                this.input=false
                $('.mask').stop().animate({ opacity: 0 }, 400)
                $('.mask').toggleClass('mask_hidden')
            })
            .fail(function(){
              $('.mask').stop().animate({ opacity: 0 }, 400)
              $('.mask').toggleClass('mask_hidden')
              alert('啊哦，服务器好像出现了错误，要不你再试一次?')
            })
        },
        choice(index,val){
          $('#textarea_'+index.toString()).text(val)
          $('#textarea_'+index.toString()).trigger("input");
        },
        get_result(){
          let temp=[]
          for(let i =0;i<this.text.length;i++){
            if(!$('#textarea_'+i.toString()).text()){
              alert('还有未填写的翻译段落！')
              return
            }
            temp.push(this.text[i][1].replace(/[\n]/g,'')+'\n'+$('#textarea_'+i.toString()).text().replace(/[\n]/g,''))
            //temp.push($('#textarea_'+i.toString()).text().replace(/[\n]/g,''))
          }
          localStorage.clear();
          copy(temp.join('\n\n'))
        },
        back(){
          this.text=JSON.parse(localStorage.getItem('origin'))
          this.input=false
          let temp=JSON.parse(localStorage.getItem('save'))
          setTimeout(
            ()=>{for(let i=0;i<temp.length;i++)if(temp[i])$('#textarea_'+i.toString()).text(temp[i])},50)
        },
        re_trans(){
          $('#translate_input').val(re_trans($('#translate_input').val()))
        }
        ,
        change(index){
          let temp='#origin_'+index.toString()
          if(!$(temp).attr('contenteditable')){
            $(temp).attr('contenteditable',true)
            $(temp).toggleClass('origin_text_change')
            $(temp).focus()
          }
          else{
            let temp2=$(temp).text()
            if(temp2.length>5000){
              alert('您输入的段落太长了，稍微缩短一下吧')
              return
            }else if(temp2.length==0){
              alert('不可以为空啊')
            }
            $(temp).attr('contenteditable',false)
            $(temp).toggleClass('origin_text_change')
            this.$set(this.text,index,[index,this.text[index][1],'翻译中...','翻译中...'])
            $.post('/translate/one',{data:temp2},(resp)=>{
                console.log(resp)
                let fool=JSON.parse(localStorage.getItem('origin'))
                fool[index]=[index,temp2,resp['youdao'],resp['google']]
                localStorage.setItem('origin',JSON.stringify(fool));
                this.text=fool
            })
            .fail(function(){
              this.$set(this.text,index,[index,this.text[index][1],'翻译失败','翻译失败'])
              alert('啊哦，服务器好像出现了错误，要不你再试一次?')
            })
          }
        }
    }
})

$(document).on('input','.change_text',function(){
  let index=Number(this.id.split('_')[1])
  temp=JSON.parse(localStorage.getItem('save'))
  temp[index]=$(this).text()
  localStorage.setItem('save',JSON.stringify(temp));
})

function re_trans(text){
  //去除参考文献
  var reg1=/\([^(]*?[1-2]{1}[0-9]{3}\)/g
  var reg2=/\([^(]*?[1-2]{1}[0-9]{3}\w\)/g
  var reg3=/\([1-2]{1}[0-9]{3}\)/g
  var reg4=/\([1-2]{1}[0-9]{3}\w\)/g
  //换行与修复
  var wr=['. ','Fig. \n','Figs. \n','vs. \n','et.al. \n','et al. \n','e.g. \n']
  var tr=['. \n','Fig. ','Figs. ','vs. ','et.al. ','et al. ','e.g. ']
  text=text.replace(reg1,'').replace(reg2,'').replace(reg3,'').replace(reg4,'')
  for(let i=0;i<wr.length;i++){
    text=text.split(wr[i]).join(tr[i])
  }
  while(text.indexOf('  ')>-1)text=text.replace('  ',' ')
  text=text.replace('\n \n','\n')
  return text
}
