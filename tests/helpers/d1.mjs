import {DatabaseSync} from 'node:sqlite';
import {readFileSync} from 'node:fs';
export function createD1(){
  const sqlite=new DatabaseSync(':memory:');sqlite.exec(readFileSync(new URL('../../analytics/schema.sql',import.meta.url),'utf8'));
  const DB={prepare(sql){return {args:[],bind(...args){this.args=args;return this;},async run(){return sqlite.prepare(sql).run(...this.args);},async all(){return {results:sqlite.prepare(sql).all(...this.args)};}};},async batch(statements){sqlite.exec('BEGIN');try{const result=[];for(const stmt of statements)result.push(await stmt.all());sqlite.exec('COMMIT');return result;}catch(error){sqlite.exec('ROLLBACK');throw error;}}};
  return {DB,sqlite};
}
