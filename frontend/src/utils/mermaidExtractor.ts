/**
 * Mermaid图表提取和转换工具
 * 用于将Markdown中的Mermaid代码块转换为PNG图片，以支持Word文档导出
 */

interface MermaidImage {
  index: number;
  code: string;
  imageData: string; // base64编码的图片数据
}

// 图片尺寸配置
const IMAGE_CONFIG = {
  maxWidth: 800,     // 最大宽度（像素）
  maxHeight: 600,    // 最大高度（像素）
  renderScale: 2,    // 高清渲染倍数
};

// 样式配置
const MERMAID_STYLES = {
  light: {
    background: 'white',
    nodeRect: { fill: '#f9f9f9', stroke: '#333' },
    text: { fill: '#333' },
    edge: { stroke: '#333' },
  },
  dark: {
    background: '#111827',
    nodeRect: { fill: '#374151', stroke: '#6b7280' },
    text: { fill: '#e5e7eb' },
    edge: { stroke: '#6b7280' },
  },
};

/**
 * 计算输出尺寸，保持宽高比
 */
function calculateOutputSize(width: number, height: number): { outputWidth: number; outputHeight: number } {
  let outputWidth = width;
  let outputHeight = height;
  
  if (width > IMAGE_CONFIG.maxWidth || height > IMAGE_CONFIG.maxHeight) {
    const scaleX = IMAGE_CONFIG.maxWidth / width;
    const scaleY = IMAGE_CONFIG.maxHeight / height;
    const scale = Math.min(scaleX, scaleY);
    outputWidth = Math.floor(width * scale);
    outputHeight = Math.floor(height * scale);
  }
  
  return { outputWidth, outputHeight };
}

/**
 * 设置SVG属性
 */
function setupSvgAttributes(
  svg: SVGElement, 
  originalWidth: number, 
  originalHeight: number,
  outputWidth: number, 
  outputHeight: number
): void {
  // 保持原始viewBox确保内容不被缩放
  if (!svg.getAttribute('viewBox')) {
    svg.setAttribute('viewBox', `0 0 ${originalWidth} ${originalHeight}`);
  }
  svg.setAttribute('width', String(outputWidth));
  svg.setAttribute('height', String(outputHeight));
}

/**
 * 应用内联样式
 */
function applyInlineStyles(svg: SVGElement, isDark: boolean): void {
  const theme = isDark ? MERMAID_STYLES.dark : MERMAID_STYLES.light;
  const styleElement = document.createElement('style');
  
  styleElement.textContent = `
    text { font-family: Arial, sans-serif; }
    .node rect { fill: ${theme.nodeRect.fill}; stroke: ${theme.nodeRect.stroke}; stroke-width: 1.5px; }
    .node polygon { fill: ${theme.nodeRect.fill}; stroke: ${theme.nodeRect.stroke}; stroke-width: 1.5px; }
    .node circle { fill: ${theme.nodeRect.fill}; stroke: ${theme.nodeRect.stroke}; stroke-width: 1.5px; }
    .edgePath path { stroke: ${theme.edge.stroke}; stroke-width: 1.5px; fill: none; }
    .label { color: ${theme.text.fill}; }
    text { fill: ${theme.text.fill}; }
  `;
  
  svg.insertBefore(styleElement, svg.firstChild);
}

/**
 * 将SVG转换为PNG数据URL
 */
async function convertToCanvas(
  svgDataUrl: string, 
  outputWidth: number, 
  outputHeight: number, 
  isDark: boolean
): Promise<string> {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      reject(new Error('无法创建canvas上下文'));
      return;
    }
    
    // 设置高分辨率画布
    canvas.width = outputWidth * IMAGE_CONFIG.renderScale;
    canvas.height = outputHeight * IMAGE_CONFIG.renderScale;
    
    // 填充背景
    const theme = isDark ? MERMAID_STYLES.dark : MERMAID_STYLES.light;
    ctx.fillStyle = theme.background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    const img = new Image();
    
    img.onload = () => {
      ctx.scale(IMAGE_CONFIG.renderScale, IMAGE_CONFIG.renderScale);
      ctx.drawImage(img, 0, 0, outputWidth, outputHeight);
      
      canvas.toBlob((blob) => {
        if (!blob) {
          reject(new Error('无法生成图片'));
          return;
        }
        
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result as string;
          resolve(base64.split(',')[1]); // 移除data:image/png;base64,前缀
        };
        reader.readAsDataURL(blob);
      }, 'image/png');
    };
    
    img.onerror = () => reject(new Error('图片加载失败'));
    img.src = svgDataUrl;
  });
}

/**
 * 从Mermaid SVG元素生成PNG图片
 */
async function svgToPng(svgElement: SVGElement, isDark: boolean): Promise<string> {
  const clonedSvg = svgElement.cloneNode(true) as SVGElement;
  
  // 获取尺寸信息
  const bbox = svgElement.getBoundingClientRect();
  const { outputWidth, outputHeight } = calculateOutputSize(bbox.width, bbox.height);
  
  // 设置SVG属性和样式
  setupSvgAttributes(clonedSvg, bbox.width, bbox.height, outputWidth, outputHeight);
  applyInlineStyles(clonedSvg, isDark);
  
  // 序列化SVG为data URL
  const svgData = new XMLSerializer().serializeToString(clonedSvg);
  const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
  const svgDataUrl = `data:image/svg+xml;base64,${svgBase64}`;
  
  // 转换为PNG
  return convertToCanvas(svgDataUrl, outputWidth, outputHeight, isDark);
}

/**
 * 创建临时容器用于渲染Mermaid
 */
function createTempContainer(): HTMLDivElement {
  const container = document.createElement('div');
  container.style.position = 'absolute';
  container.style.left = '-9999px';
  container.style.top = '-9999px';
  document.body.appendChild(container);
  return container;
}

/**
 * 提取并转换Mermaid图表
 * @param content Markdown内容
 * @param isDark 是否为暗色主题
 * @returns 内容和图片数组
 */
export async function extractAndConvertMermaidDiagrams(
  content: string,
  isDark: boolean = false
): Promise<{ content: string; images: MermaidImage[] }> {
  const images: MermaidImage[] = [];
  
  // 查找所有Mermaid代码块
  const mermaidRegex = /```mermaid\n([\s\S]*?)```/g;
  const matches = Array.from(content.matchAll(mermaidRegex));
  
  if (matches.length === 0) {
    return { content, images };
  }
  
  const tempContainer = createTempContainer();
  
  try {
    // 动态导入mermaid
    const mermaid = (await import('mermaid')).default;
    
    // 初始化mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? 'dark' : 'default',
      securityLevel: 'loose',
    });
    
    // 处理每个Mermaid代码块
    for (let i = 0; i < matches.length; i++) {
      const mermaidCode = matches[i][1].trim();
      
      try {
        // 渲染Mermaid图表
        const graphId = `mermaid-export-${Date.now()}-${i}`;
        const { svg } = await mermaid.render(graphId, mermaidCode);
        
        // 获取SVG元素
        tempContainer.innerHTML = svg;
        const svgElement = tempContainer.querySelector('svg');
        
        if (svgElement) {
          // 转换为PNG
          const imageData = await svgToPng(svgElement, isDark);
          images.push({
            index: i,
            code: mermaidCode,
            imageData,
          });
        }
      } catch (error) {
        console.error(`转换Mermaid图表 ${i} 失败:`, error);
      }
    }
  } finally {
    // 清理临时容器
    document.body.removeChild(tempContainer);
  }
  
  return { content, images };
}