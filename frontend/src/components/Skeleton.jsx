export function Skeleton({ width = '100%', height = 14, style }) {
  return <span className="skeleton" style={{ display: 'block', width, height, ...style }} />
}

export function SkeletonRows({ rows = 6, cols = 4 }) {
  return Array.from({ length: rows }).map((_, r) => (
    <tr key={r}>
      {Array.from({ length: cols }).map((__, c) => (
        <td key={c}>
          <Skeleton width={c === 0 ? '60%' : '40%'} />
        </td>
      ))}
    </tr>
  ))
}
