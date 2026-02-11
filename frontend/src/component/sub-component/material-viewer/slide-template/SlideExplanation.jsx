import { useState, useEffect } from 'react';
import '../../../../styles.css';
import '../../../../dashboard.css';
import axios from 'axios'

/*  slide: {subtitle: conclusion,
            content: conclusion point form,
            slide_type: explanation,
            page:4} */
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
      <div className="slide-footer">
        <p>Page {slide.page}</p>
      </div>
    </div>
  );
}

export default SlideExplanation;
