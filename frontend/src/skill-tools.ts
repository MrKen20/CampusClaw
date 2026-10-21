export function addToolReference(source:string,ref:string):string {
 source=source.replace(/\r\n/g,'\n')
 const split=source.indexOf('\n\n'),head=split<0?source:source.slice(0,split),body=split<0?'':source.slice(split)
 const line=/^[ \t]*工具[ \t]*[：:][ \t]*(.*)$/m,match=line.exec(head)
 if(match){const refs=match[1].split(/[,，、;；|]/).map(v=>v.trim()).filter(Boolean);if(!refs.includes(ref))refs.push(ref);return head.replace(line,'工具：'+refs.join(','))+body}
 return head.trimEnd()+'\n工具：'+ref+body
}
