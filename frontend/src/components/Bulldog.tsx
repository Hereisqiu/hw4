// Pure HTML/CSS bulldog mascot ("Dan"), used as the chat launcher and avatar.
export default function Bulldog({ size = 56, mood = 'happy' }: { size?: number; mood?: 'happy' | 'thinking' }) {
  return (
    <span className={`bulldog ${mood}`} style={{ fontSize: size / 56 + 'rem' }} aria-hidden="true">
      <span className="bd-ear left" />
      <span className="bd-ear right" />
      <span className="bd-head">
        <span className="bd-brow left" />
        <span className="bd-brow right" />
        <span className="bd-eye left" />
        <span className="bd-eye right" />
        <span className="bd-muzzle">
          <span className="bd-nose" />
          <span className="bd-mouth" />
          <span className="bd-tooth left" />
          <span className="bd-tooth right" />
        </span>
      </span>
      <span className="bd-collar"><span className="bd-tag">Y</span></span>
    </span>
  )
}
