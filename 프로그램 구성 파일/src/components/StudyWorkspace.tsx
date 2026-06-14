import type { CSSProperties, MouseEvent, ReactNode } from 'react'
import type { ThemeMode } from '../types'

export function StudyWorkspace({
  themeMode,
  showSetPanel,
  showSidePanel,
  setPanelWidth,
  sidePanelWidth,
  textScale,
  glareLevel,
  rail,
  setPanel,
  children,
  sidePanel,
  onSetPanelResizeStart,
  onSidePanelResizeStart,
}: {
  themeMode: ThemeMode
  showSetPanel: boolean
  showSidePanel: boolean
  setPanelWidth: number
  sidePanelWidth: number
  textScale: number
  glareLevel: number
  rail: ReactNode
  setPanel: ReactNode
  children: ReactNode
  sidePanel: ReactNode
  onSetPanelResizeStart: (event: MouseEvent<HTMLDivElement>) => void
  onSidePanelResizeStart: (event: MouseEvent<HTMLDivElement>) => void
}) {
  const className = [
    'final-shell',
    `theme-${themeMode}`,
    showSetPanel ? 'with-set-panel' : '',
    showSidePanel ? 'with-side-panel' : '',
  ]
    .filter(Boolean)
    .join(' ')
  const readableText = themeMode === 'dark' ? Math.max(112, Math.round(222 - glareLevel * 90)) : 25
  const imageBrightness = Math.max(0.25, 1 - glareLevel * 0.62)
  const imageContrast = Math.max(0.62, 1 - glareLevel * 0.22)
  const imageSaturate = Math.max(0.58, 1 - glareLevel * 0.22)

  return (
    <main
      className={className}
      style={
        {
          '--set-panel-width': `${setPanelWidth}px`,
          '--side-panel-width': `${sidePanelWidth}px`,
          '--study-text-scale': textScale,
          '--study-readable-text':
            themeMode === 'dark' ? `rgb(${readableText}, ${readableText}, ${readableText})` : 'var(--text)',
          '--study-image-filter':
            themeMode === 'dark'
              ? `brightness(${imageBrightness}) contrast(${imageContrast}) saturate(${imageSaturate})`
              : 'none',
        } as CSSProperties
      }
    >
      {rail}
      {showSetPanel && (
        <section className="set-panel-shell">
          {setPanel}
          <div className="resize-handle right" onMouseDown={onSetPanelResizeStart} />
        </section>
      )}
      <section className="study-main">{children}</section>
      {showSidePanel && (
        <section className="side-panel-shell">
          <div className="resize-handle left" onMouseDown={onSidePanelResizeStart} />
          {sidePanel}
        </section>
      )}
    </main>
  )
}
