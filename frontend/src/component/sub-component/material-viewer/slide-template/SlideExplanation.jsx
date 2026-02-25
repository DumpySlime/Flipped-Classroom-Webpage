import { useState, useEffect } from 'react';
import '../../../../styles.css';
import '../../../../dashboard.css';
import axios from 'axios'

/*  slide: {subtitle: conclusion,
            content: conclusion point form,
            slide_type: explanation,
            page: 4,
            url: video url} */
function SlideExplanation ({ slide }) {
  // ensure content is in array format
  const contentList = Array.isArray(slide.content) ? slide.content : [slide.content];
  
  return (
    <div className="slide-explanation">
      <h1>{slide.subtitle}</h1>
      <ul>
        {contentList.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
      <div className="slide-video" style={{ display: slide.url ? 'block' : 'none' }}>
        <video controls>
          <source src={slide.url} type="video/mp4" />
          Your browser does not support the video tag.
        </video>
      </div>
      <div className="slide-footer">
        <p>Page {slide.page}</p>
      </div>
    </div>
  );
}

export default SlideExplanation;
