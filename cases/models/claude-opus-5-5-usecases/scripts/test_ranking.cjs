const assert = require('node:assert/strict');
const {test} = require('node:test');
const {assign, signal} = require('./ranking.js');
test('PR and issue rank independently of parent stars and repositories', () => {
  const cases = [
    {source:'github',githubKind:'repository',stars:100},
    {source:'github',githubKind:'repository',stars:1000},
    {source:'github',githubKind:'pull_request',stars:900000,reactions:0,comments:1000},
    {source:'github',githubKind:'pull_request',stars:1,reactions:5},
    {source:'github',githubKind:'file',stars:999999},
    {source:'github',githubKind:'issue',reactions:2}
  ];
  assign(cases);
  assert.equal(cases[2]._hot, 0);
  assert.equal(cases[3]._hot, 1);
  assert.equal(cases[4]._hot, -1);
  assert.equal(cases[5]._hot, 0.5);
  const before = cases.map(c => c._hot);
  cases[2].stars = 999999999;
  cases[2].comments = 999999;
  assign(cases);
  assert.deepEqual(cases.map(c => c._hot), before);
});
test('ties are equal regardless of input order; zero and unknown remain distinct', () => {
  const cases = [0,0,1,1,4,null,undefined,NaN,-1].map((likes,i)=>({id:i,source:'x',likes}));
  assign(cases);
  assert.deepEqual(cases.map(c=>c._hot), [0,0,.625,.625,1,-1,-1,-1,-1]);
  const scores = Object.fromEntries(cases.map(c=>[c.id,c._hot]));
  assign(cases.reverse());
  assert.deepEqual(Object.fromEntries(cases.map(c=>[c.id,c._hot])), scores);
  assert.deepEqual(assign([0,0,0].map(reactions=>({source:'github',githubKind:'issue',reactions}))).map(c=>c._hot),[0,0,0]);
});
test('a video with only likes never competes against video plays', () => {
  assert.deepEqual(signal({source:'video',views:0,likes:400}), ['video:views',0]);
  assert.deepEqual(signal({source:'video',likes:400}), ['video:likes',400]);
  const cases = [{source:'video',views:1000},{source:'video',views:2000},{source:'video',likes:1}];
  assign(cases);
  assert.equal(cases[2]._hot,.5);
});
