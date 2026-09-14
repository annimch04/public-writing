import test from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import {extractionScript} from '../tools/x_safari_scraper.mjs';

function extract(author,quoteAuthor){
 const anchor=(user,id,timed)=>({getAttribute:()=>`/${user}/status/${id}`,querySelector:()=>timed?{getAttribute:()=> '2026-09-14T12:00:00.000Z'}:null});
 const anchors=[anchor(author,'100',true),...(quoteAuthor?[anchor(quoteAuthor,'99',false)]:[])];
 const article={innerText:'Public authored text',querySelectorAll:selector=>selector.startsWith('a[')?anchors:[],querySelector:selector=>selector.includes('tweetText')?{innerText:'Public authored text'}:null};
 const document={querySelectorAll:()=>[article],querySelector:()=>null,body:{innerText:'Public profile'}};
 return JSON.parse(vm.runInNewContext(extractionScript('SayitSalty'),{document}));
}
test('a third-party post quoting Anni is not attributed to Anni',()=>{
 assert.equal(extract('OtherAuthor','SayitSalty').posts.length,0);
});
test('Anni quoting another account retains her text and status identity',()=>{
 const result=extract('SayitSalty','OtherAuthor');
 assert.equal(result.posts.length,1);assert.equal(result.posts[0].id,'100');
 assert.equal(result.posts[0].text,'Public authored text');
});
