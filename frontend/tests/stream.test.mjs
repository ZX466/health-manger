// SSE 终态回归：只有完整解析的 done/error 帧才算正常结束。
import test from 'node:test'
import assert from 'node:assert/strict'
import { streamChatMessage } from '../src/api/stream.js'

globalThis.localStorage = {
  getItem: () => 'test-token',
  removeItem: () => {},
  setItem: () => {}
}

function mockFetch (chunks) {
  globalThis.fetch = async () => new Response(
    new ReadableStream({
      start (controller) {
        const encoder = new TextEncoder()
        for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
        controller.close()
      }
    }),
    { status: 200, headers: { 'Content-Type': 'text/event-stream' } }
  )
}

async function collect (chunks) {
  mockFetch(chunks)
  const events = []
  let error = null
  try {
    await streamChatMessage(1, 'hi', {
      onEvent: (event, data) => events.push([event, data])
    })
  } catch (e) {
    error = e
  }
  return { events, error }
}

test('完整 done 帧正常结束', async () => {
  const { events, error } = await collect([
    'event: delta\ndata: {"content":"你"}\n\n',
    'event: done\ndata: {"message_id":7,"tokens_used":3}\n\n'
  ])
  assert.equal(error, null)
  assert.deepEqual(events.map(([name]) => name), ['delta', 'done'])
})

test('截断的 done 帧按中断处理且不回调 done', async () => {
  const { events, error } = await collect([
    'event: delta\ndata: {"content":"半"}\n\n',
    'event: done\ndata: {"message_id":7,'
  ])
  assert.equal(error?.code, 'STREAM_INCOMPLETE')
  assert.deepEqual(events.map(([name]) => name), ['delta'])
})

test('done 帧缺少结束空行按中断处理', async () => {
  const { events, error } = await collect([
    'event: delta\ndata: {"content":"半"}\n\n',
    'event: done\ndata: {"message_id":7,"tokens_used":3}\n'
  ])
  assert.equal(error?.code, 'STREAM_INCOMPLETE')
  assert.deepEqual(events.map(([name]) => name), ['delta'])
})

test('done 数据为 null 或缺少契约字段按中断处理', async () => {
  for (const payload of ['null', '{}', '{"message_id":7}']) {
    const { events, error } = await collect([
      `event: done\ndata: ${payload}\n\n`
    ])
    assert.equal(error?.code, 'STREAM_INCOMPLETE', payload)
    assert.deepEqual(events, [], payload)
  }
})

test('缺少终态按中断处理', async () => {
  const { error } = await collect([
    'event: delta\ndata: {"content":"半"}\n\n'
  ])
  assert.equal(error?.code, 'STREAM_INCOMPLETE')
})

test('error 帧正常结束', async () => {
  const { events, error } = await collect([
    'event: error\ndata: {"detail":"上游失败"}\n\n'
  ])
  assert.equal(error, null)
  assert.deepEqual(events.map(([name]) => name), ['error'])
})

test('error 数据为 null 按中断处理且不回调', async () => {
  const { events, error } = await collect([
    'event: error\ndata: null\n\n'
  ])
  assert.equal(error?.code, 'STREAM_INCOMPLETE')
  assert.deepEqual(events, [])
})
