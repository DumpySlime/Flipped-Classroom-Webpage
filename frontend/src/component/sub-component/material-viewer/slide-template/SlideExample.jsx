import { useState, useEffect } from 'react';
import '../../../../styles.css';
import '../../../../dashboard.css';
import axios from 'axios'
import { useTranslation } from 'react-i18next';

/*  slide: {subtitle: conclusion,
            content: conclusion point form,
            slide_type: explanation,
            page:4} */
function SlideExample ({ slide }) {
  const { t } = useTranslation();
  // Process the content to ensuree it's in cluster format
  const contentArray = Array.isArray(slide.content) ? slide.content : [slide.content];
  
  // title as the first line
  const question = contentArray[0] || '';
  
  // remaining lines as solution steps
  const solutionSteps = contentArray.slice(1);
  
  return (
    <div className="slide-example">
      <h1>{slide.subtitle}</h1>
      <div className="example-body">
        <div className="example-left">
          <h2>{t('question')}</h2>
          <p>{question}</p>
        </div>
        <div className="example-right">
          <h2>{t('solutionSteps')}</h2>
          <ul>
            {solutionSteps.map((step, index) => (
              <li key={index}>{step}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="slide-footer">
        <p>{t('pageX', { x: slide.page })}</p>
      </div>
    </div>
  );
}

export default SlideExample;
