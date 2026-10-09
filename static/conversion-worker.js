import { MAX_BYTES, readGpx, summary, convert } from './browser-converter.mjs';
self.onmessage=async({data:{file,mode,config}})=>{
  try {
    if(file.size>MAX_BYTES)throw new Error('GPX 文件不能超过 16 MB。');
    const buffer=await file.arrayBuffer(),bytes=new Uint8Array(buffer);
    const encoding=bytes[0]===255&&bytes[1]===254?'utf-16le':bytes[0]===254&&bytes[1]===255?'utf-16be':'utf-8';
    const xml=new TextDecoder(encoding,{fatal:true}).decode(buffer);
    if(mode==='preview')self.postMessage({result:summary(readGpx(xml))});
    else {const converted=convert(xml,config,progress=>self.postMessage({progress}));self.postMessage(converted,[converted.data.buffer]);}
  } catch(error){self.postMessage({error:error.message,field:error.field||'file'});}
};
